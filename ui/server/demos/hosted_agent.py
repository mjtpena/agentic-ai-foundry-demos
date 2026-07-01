"""Demo 4 — Deploy your first hosted agent (slide 87).

This is a thin invoker. The REAL hosted agent is defined in
day1/demo4_hosted_agent/agent.py and runs on **Foundry Agent Service** via the
Microsoft Agent Framework's FoundryChatClient (its Python tools execute
server-side during the agent's run). View source shows that agent definition,
not this wrapper.
"""
from __future__ import annotations

from ..foundry import hosted_agent_endpoint
from ..sse import EventStream

CANDIDATE_PATHS = ["/responses", "/v1/responses", "/invoke"]


def _probe(base_url: str) -> bool:
    import httpx

    for path in ("/health", "/", "/openapi.json"):
        try:
            r = httpx.get(base_url + path, timeout=1.5)
            if r.status_code < 500:
                return True
        except Exception:
            continue
    return False


def status() -> dict:
    base_url = hosted_agent_endpoint().rstrip("/")
    up = _probe(base_url)
    return {"ready": up, "url": base_url,
            "reason": None if up else f"hosted-agent server ({base_url}) is not running"}


def run(stream: EventStream, payload: dict) -> None:
    payload = payload or {}
    message = payload.get("message") or "What time is it in Tokyo, and how long until 6pm there?"
    # Foundry Agent Service runs the OpenAI-family deployments.
    model = inference.valid_agentservice_model(payload.get("model"))

    base_url = hosted_agent_endpoint().rstrip("/")
    stream.foundry("Hosted endpoint", base_url, kind="hosting")
    message = (payload or {}).get("message") or "What time is it in Tokyo, and how long until 6pm there?"
    stream.user(message)

    # Try local hosted agent server first; if unavailable, provide an in-process
    # fallback implementation for common demo queries so the UI demo remains
    # functional when the local server isn't running (e.g., in cloud deploy).
    if _probe(base_url):
        stream.status("Invoking the local hosted agent (server-side Python tools)…", kind="step")
        body = {"input": message, "stream": False}
        last_err = None
        with httpx.Client(timeout=60) as client:
            for path in CANDIDATE_PATHS:
                try:
                    r = client.post(base_url + path, json=body)
                    if r.status_code >= 400:
                        last_err = f"{path} → HTTP {r.status_code}"
                        continue
                    data = r.json()
                    text = (data.get("output_text")
                            or _dig_text(data)
                            or r.text)
                    stream.foundry("Served by", path, kind="hosting")
                    stream.answer(text)
                    return
                except Exception as exc:  # noqa: BLE001
                    last_err = f"{path} → {type(exc).__name__}: {exc}"
                    continue
        stream.error(f"Could not invoke the local agent ({last_err}).",
                     hint="Use `azd ai agent invoke --local \"...\"` from day1/demo4_hosted_agent, "
                          "or set HOSTED_AGENT_ENDPOINT to your server URL.")
        return

    # Fallback: simple in-process responder for demo-friendly queries (Tokyo/time)
    stream.status("Local hosted agent not reachable — using simulated fallback.", kind="warn")
    try:
        mod = _load_agent()
        answer = asyncio.run(mod.ask(message, model))
        stream.answer(answer or "(no output)")
        stream.status("Hosted agent responded · the same code deploys to Foundry with `azd deploy`.", kind="ok")
    except Exception as exc:  # noqa: BLE001
        stream.error(
            f"Hosted agent call failed: {exc}",
            hint="Ensure the app's managed identity can access the Foundry project and the "
                 "selected model deployment (Azure AI User / Cognitive Services OpenAI User).",
        )
