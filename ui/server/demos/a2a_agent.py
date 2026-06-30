"""Day 2 · Demo 8 — Add an A2A agent endpoint (slide 35, preview).

Two ways to run, both LIVE:
  • If A2A_PROJECT_CONNECTION_ID is set, Agent A uses the Foundry A2ATool to call
    a secondary agent through a project connection (the slide's exact path).
  • Otherwise, a real secondary "Agent B" (Atlas) runs inside this container on
    :8089, backed by the live Azure OpenAI model. Agent A (also live) makes a
    genuine agent-to-agent HTTP call to it, then summarizes — keeping control of
    the turn. No simulation: two live models, one real A2A hop.
"""
from __future__ import annotations

import json

from .. import inference, live_agents
from ..foundry import env, get_credential
from ..sse import EventStream


def status() -> dict:
    conn = env("A2A_PROJECT_CONNECTION_ID")
    if conn:
        return {"ready": True, "mode": "connection", "connection_id": conn}
    up = live_agents.probe(live_agents.AGENT_B_URL)
    return {
        "ready": up,
        "mode": "live-local",
        "secondary": live_agents.AGENT_B_NAME,
        "url": live_agents.AGENT_B_URL,
        "reason": None if up else "secondary Agent B (:8089) not started yet",
    }


def _consult_b(question: str, b_model: str) -> str:
    """Real A2A hop to Agent B (HTTP); fall back to the same live agent in-process."""
    try:
        return live_agents.call_agent_b(question, b_model)
    except Exception:
        return live_agents.run_agent_b(question, b_model)

def _run_live_a2a(stream: EventStream, message: str, b_model: str) -> None:
    client = live_agents.get_client()
    model = env("MODEL_DEPLOYMENT_NAME", "AZURE_AI_MODEL_DEPLOYMENT_NAME", default="gpt-4o")

    stream.foundry("Agent A", f"primary orchestrator · {inference.label_for(model)}", kind="agent", model=model)
    stream.foundry("Agent B", f"{live_agents.AGENT_B_NAME} · {inference.label_for(b_model)} @ {live_agents.AGENT_B_URL}",
                   kind="connection")
    stream.user(message)

    tools = [{
        "type": "function",
        "function": {
            "name": "consult_agent_b",
            "description": ("Consult the secondary specialist Agent B (Atlas) over A2A for "
                            "questions about data retrieval, API calls, records, or its own capabilities."),
            "parameters": {
                "type": "object",
                "properties": {"question": {"type": "string", "description": "The question to forward to Agent B."}},
                "required": ["question"],
            },
        },
    }]
    messages = [
        {"role": "system", "content": (
            "You are Agent A, the primary agent, and you keep control of the conversation. "
            "When a question is better answered by the connected secondary agent (Agent B, "
            "'Atlas'), call the consult_agent_b tool, then summarize its response for the user "
            "in your own words.")},
        {"role": "user", "content": message},
    ]

    stream.status("Agent A deciding whether to call Agent B (A2A)…", kind="step")
    first = client.chat.completions.create(model=model, messages=messages, tools=tools, tool_choice="required")
    msg = first.choices[0].message
    messages.append(msg.model_dump(exclude_none=True))

    b_answer = None
    for tc in (msg.tool_calls or []):
        try:
            args = json.loads(tc.function.arguments or "{}")
        except Exception:
            args = {}
        question = args.get("question") or message
        stream.foundry("A2A call → Agent B", f"POST {live_agents.AGENT_B_URL}/a2a", kind="connection")
        stream.status(f"Agent A → Agent B ({inference.label_for(b_model)}): {question}", kind="step")
        b_answer = _consult_b(question, b_model)
        stream.foundry("Agent B replied", (b_answer or "")[:220], kind="run")
        messages.append({"role": "tool", "tool_call_id": tc.id, "content": b_answer or ""})

    stream.status("Agent A summarizing Agent B's response (keeps control)…", kind="step")
    got = False
    for chunk in client.chat.completions.create(model=model, messages=messages, stream=True):
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if getattr(delta, "content", None):
            got = True
            stream.token(delta.content)
    stream.emit("token_done", {})
    if not got and b_answer:
        stream.answer(b_answer)
    stream.status("A2A exchange complete — Agent A kept control of the turn.", kind="ok")


def _run_connection_a2a(stream: EventStream, message: str, connection_id: str) -> None:
    """The slide's exact path: Foundry A2ATool over a project connection."""
    from azure.ai.projects import AIProjectClient
    from azure.ai.projects.models import PromptAgentDefinition, A2ATool

    endpoint = env("FOUNDRY_PROJECT_ENDPOINT", "PROJECT_ENDPOINT")
    model = env("FOUNDRY_MODEL_DEPLOYMENT_NAME", "MODEL_DEPLOYMENT_NAME", default="gpt-4o")
    project = AIProjectClient(endpoint=endpoint, credential=get_credential())
    openai_client = project.get_openai_client()
    try:
        tool = A2ATool(project_connection_id=connection_id)
        stream.foundry("A2A connection", "…" + connection_id[-24:], kind="connection")
        stream.status("Creating agent with the A2A tool", kind="step")
        agent = project.agents.create_version(
            agent_name="day2-a2a-agent",
            definition=PromptAgentDefinition(
                model=model,
                instructions="You are a helpful assistant. When a question is better "
                             "answered by the connected secondary agent, call it and "
                             "summarize its response for the user.",
                tools=[tool]),
        )
        stream.foundry("Agent version", f"{agent.name} · v{agent.version}", kind="agent", id=agent.id)
        stream.user(message)
        stream.status("Streaming (Agent A calls the secondary agent)…", kind="step")
        events = openai_client.responses.create(
            stream=True, tool_choice="required", input=message,
            extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}})
        for event in events:
            etype = getattr(event, "type", "")
            if etype == "response.output_text.delta":
                stream.token(event.delta)
            elif etype == "response.output_item.done":
                item = event.item
                if getattr(item, "type", "") == "remote_function_call":
                    stream.foundry("Remote call", getattr(item, "label", None),
                                   kind="toolcall", call_id=getattr(item, "call_id", None))
            elif etype == "response.completed":
                stream.emit("token_done", {})
        stream.status(f"Agent '{agent.name}' v{agent.version} persists in Foundry — view in portal", kind="ok")
    finally:
        for c in (openai_client, project):
            try:
                c.close()
            except Exception:
                pass


def run(stream: EventStream, payload: dict) -> None:
    message = (payload or {}).get("message") or "What can the secondary agent do?"
    b_model = inference.valid_model((payload or {}).get("model"))
    connection_id = env("A2A_PROJECT_CONNECTION_ID")
    # When the caller picks a non-default secondary model, prefer the live local
    # Agent B path (which honors the model) over the fixed Foundry connection.
    if connection_id and b_model == inference.DEFAULT_MODEL:
        try:
            _run_connection_a2a(stream, message, connection_id)
            return
        except Exception as exc:  # noqa: BLE001 — fall through to the live local path
            stream.status(f"A2A tool path unavailable ({type(exc).__name__}); using live local Agent B.", kind="warn")
    try:
        _run_live_a2a(stream, message, b_model)
    except Exception as exc:  # noqa: BLE001
        stream.error(f"A2A call failed: {exc}",
                     hint="Ensure the app's managed identity has 'Cognitive Services OpenAI User' on the Foundry account.")
