"""Live, in-container agent servers — make demos 4 (hosted agent) and 8 (A2A)
genuinely live instead of simulated.

Two small HTTP servers run as daemon threads inside the same container, each
backed by the LIVE Azure OpenAI model on the Foundry account endpoint
(authenticated with the container's managed identity, same as every other live
demo):

  • :8088  Hosted agent — a code-based agent with two real Python tools
           (`get_local_date_time`, `hours_until`). The model does real
           tool-calling; the tools execute server-side. This is exactly what the
           hosted-agent demo probes for and invokes over HTTP.

  • :8089  "Agent B" (Atlas) — a secondary specialist agent that publishes an
           A2A AgentCard at /.well-known/agent.json and answers over /a2a. The
           A2A demo's Agent A makes a real agent-to-agent HTTP call to it.

Both bind to 127.0.0.1 (internal only — the app's single ingress stays :8000).
Everything here is best-effort: if a model call or a server fails, callers fall
back gracefully so a demo degrades rather than crashing the console.
"""
from __future__ import annotations

import json
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from zoneinfo import ZoneInfo

from . import inference
from .foundry import env

HOSTED_PORT = 8088
AGENT_B_PORT = 8089
HOSTED_URL = f"http://127.0.0.1:{HOSTED_PORT}"
AGENT_B_URL = f"http://127.0.0.1:{AGENT_B_PORT}"

API_VERSION = "2024-10-21"
_TOKEN_SCOPE = "https://cognitiveservices.azure.com/.default"

_client_lock = threading.Lock()
_client = None
_started = False


# --------------------------------------------------------------------------- #
# Live Azure OpenAI client (managed identity) — shared by both agents
# --------------------------------------------------------------------------- #
def _model() -> str:
    return env("MODEL_DEPLOYMENT_NAME", "AZURE_AI_MODEL_DEPLOYMENT_NAME", default="gpt-4o")


def get_client():
    """Cached AzureOpenAI client authenticated with DefaultAzureCredential."""
    global _client
    with _client_lock:
        if _client is not None:
            return _client
        from openai import AzureOpenAI
        from azure.identity import DefaultAzureCredential, get_bearer_token_provider

        endpoint = env("FOUNDRY_ACCOUNT_ENDPOINT")
        if not endpoint:
            raise RuntimeError("FOUNDRY_ACCOUNT_ENDPOINT is not set")
        provider = get_bearer_token_provider(DefaultAzureCredential(), _TOKEN_SCOPE)
        _client = AzureOpenAI(
            azure_endpoint=endpoint,
            azure_ad_token_provider=provider,
            api_version=env("AZURE_OPENAI_API_VERSION", default=API_VERSION),
        )
        return _client


# --------------------------------------------------------------------------- #
# Hosted agent — real Python tools + real tool-calling loop
# --------------------------------------------------------------------------- #
HOSTED_INSTRUCTIONS = (
    "You are a helpful assistant that can tell users the current date and time in "
    "any location and how long until a given hour there. When a user asks about "
    "time in a city, map it to the correct IANA timezone and use the appropriate "
    "tool. Call only ONE tool at a time and wait for its result before calling "
    "another (do not request multiple tool calls in a single step). Be concise."
)


def _get_local_date_time(iana_timezone: str) -> str:
    try:
        now = datetime.now(ZoneInfo(iana_timezone))
        return f"The current date and time in {iana_timezone} is " + now.strftime(
            "%A, %B %d, %Y at %I:%M %p %Z"
        )
    except Exception as e:  # noqa: BLE001
        return f"Error: unable to get time for timezone '{iana_timezone}'. {e}"


def _hours_until(iana_timezone: str, target_hour_24: int) -> str:
    try:
        now = datetime.now(ZoneInfo(iana_timezone))
        target = now.replace(hour=int(target_hour_24) % 24, minute=0, second=0, microsecond=0)
        delta_h = (target - now).total_seconds() / 3600
        if delta_h < 0:
            delta_h += 24
        return f"About {delta_h:.1f} hours until {int(target_hour_24):02d}:00 in {iana_timezone}."
    except Exception as e:  # noqa: BLE001
        return f"Error: {e}"


_HOSTED_DISPATCH = {
    "get_local_date_time": lambda a: _get_local_date_time(a.get("iana_timezone", "")),
    "hours_until": lambda a: _hours_until(a.get("iana_timezone", ""), a.get("target_hour_24", 0)),
}


def _hosted_tools():
    from azure.ai.inference.models import ChatCompletionsToolDefinition, FunctionDefinition

    return [
        ChatCompletionsToolDefinition(function=FunctionDefinition(
            name="get_local_date_time",
            description="Get the current date and time for a given IANA timezone.",
            parameters={"type": "object", "properties": {
                "iana_timezone": {"type": "string", "description": 'IANA tz, e.g. "Asia/Tokyo".'}},
                "required": ["iana_timezone"]})),
        ChatCompletionsToolDefinition(function=FunctionDefinition(
            name="hours_until",
            description="Compute how many hours remain until a target hour (0-23) in a timezone.",
            parameters={"type": "object", "properties": {
                "iana_timezone": {"type": "string"},
                "target_hour_24": {"type": "integer", "description": "Target hour, 0-23."}},
                "required": ["iana_timezone", "target_hour_24"]})),
    ]


def run_hosted_agent(message: str, model: str | None = None) -> dict:
    """Run the hosted agent on the chosen model with real tool-calling.

    Routed through the unified Azure AI inference client so the hosted agent can
    run on any tool-capable deployment (gpt-4o, Llama-3.3-70B, Mistral-Large-3…).
    Returns {"output_text", "tool_calls": [...], "model"}.
    """
    from azure.ai.inference.models import SystemMessage, UserMessage, AssistantMessage, ToolMessage

    model = inference.valid_model(model, tools_required=True)
    tools = _hosted_tools()
    messages = [SystemMessage(content=HOSTED_INSTRUCTIONS), UserMessage(content=message)]
    tool_log: list[dict] = []
    last = None
    for _ in range(6):
        resp = inference.complete(model, messages, tools=tools, tool_choice="auto", max_tokens=600)
        last = resp.choices[0].message
        if not last.tool_calls:
            break
        # Handle ONE tool call per turn: several non-OpenAI models (Llama, Mistral)
        # reject more than one tool call in a single request, so we echo a single
        # call and let the loop pick up any further calls on the next turn.
        tc = last.tool_calls[0]
        messages.append(AssistantMessage(tool_calls=[tc]))
        try:
            args = json.loads(tc.function.arguments or "{}")
        except Exception:
            args = {}
        fn = _HOSTED_DISPATCH.get(tc.function.name)
        result = fn(args) if fn else f"Unknown tool {tc.function.name}"
        tool_log.append({"name": tc.function.name, "args": args, "result": result})
        messages.append(ToolMessage(content=str(result), tool_call_id=tc.id))
    return {"output_text": (last.content if last else "") or "", "tool_calls": tool_log, "model": model}


# --------------------------------------------------------------------------- #
# Agent B (Atlas) — secondary A2A specialist
# --------------------------------------------------------------------------- #
AGENT_B_NAME = "Atlas"
AGENT_B_INSTRUCTIONS = (
    "You are Atlas, a specialist data & records agent (Agent B) reachable over the "
    "Agent-to-Agent (A2A) protocol. You focus on retrieving records, calling backend "
    "APIs, and returning structured, factual data. Answer concisely. If asked what "
    "you can do, list your concrete capabilities."
)

AGENT_B_CARD = {
    "name": AGENT_B_NAME,
    "description": "Secondary specialist agent: data retrieval, API calls, structured records.",
    "version": "1.0.0",
    "protocol": "a2a",
    "url": AGENT_B_URL + "/a2a",
    "capabilities": {"streaming": False, "skills": ["records.lookup", "api.call", "data.summarize"]},
}


def run_agent_b(message: str, model: str | None = None) -> str:
    """Agent B answers with the chosen model in its specialist persona.

    Plain chat (no tools), so it runs on ANY deployed model — that's the demo:
    the secondary agent can run on Llama / Mistral / Phi while Agent A stays on
    gpt-4o."""
    from azure.ai.inference.models import SystemMessage, UserMessage

    model = inference.valid_model(model)
    resp = inference.complete(
        model,
        [SystemMessage(content=AGENT_B_INSTRUCTIONS), UserMessage(content=message)],
        max_tokens=500,
    )
    return resp.choices[0].message.content or ""


def call_agent_b(message: str, model: str | None = None, timeout: float = 60.0) -> str:
    """Make a real A2A HTTP call to the secondary Agent B server (on `model`)."""
    import httpx

    r = httpx.post(AGENT_B_URL + "/a2a", json={"message": message, "model": model}, timeout=timeout)
    r.raise_for_status()
    return r.json().get("output_text", "")


# --------------------------------------------------------------------------- #
# HTTP plumbing
# --------------------------------------------------------------------------- #
class _Handler(BaseHTTPRequestHandler):
    role = "hosted"  # overridden per server

    def log_message(self, *args):  # silence default stderr access log
        return

    def _send(self, code: int, obj: dict):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.role == "agent_b" and self.path.startswith("/.well-known/agent"):
            return self._send(200, AGENT_B_CARD)
        # /health, /, /openapi.json all signal "up" to probes.
        return self._send(200, {"status": "ok", "agent": self.role})

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length", 0) or 0)
            raw = self.rfile.read(n) if n else b"{}"
            data = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            data = {}
        message = (data.get("input") or data.get("message") or "").strip()
        model = data.get("model")
        try:
            if self.role == "agent_b":
                self._send(200, {"output_text": run_agent_b(message, model),
                                 "agent": AGENT_B_NAME, "model": inference.valid_model(model)})
            else:
                self._send(200, run_hosted_agent(message, model))
        except Exception as e:  # noqa: BLE001 — surface as JSON, don't crash the thread
            self._send(500, {"error": f"{type(e).__name__}: {e}"})


def _make_handler(role_name: str):
    return type(f"_Handler_{role_name}", (_Handler,), {"role": role_name})


def _serve(port: int, role_name: str):
    srv = ThreadingHTTPServer(("127.0.0.1", port), _make_handler(role_name))
    srv.daemon_threads = True
    srv.serve_forever()


def start_servers() -> None:
    """Start both live agent servers as daemon threads. Idempotent, non-fatal."""
    global _started
    if _started:
        return
    _started = True
    for port, role in ((HOSTED_PORT, "hosted"), (AGENT_B_PORT, "agent_b")):
        try:
            t = threading.Thread(target=_serve, args=(port, role), daemon=True,
                                 name=f"live-agent-{role}")
            t.start()
        except Exception as e:  # noqa: BLE001
            import sys
            print(f"[live_agents] failed to start {role} on :{port}: {e}", file=sys.stderr)


def probe(url: str, timeout: float = 1.5) -> bool:
    import httpx

    try:
        return httpx.get(url + "/health", timeout=timeout).status_code < 500
    except Exception:
        return False
