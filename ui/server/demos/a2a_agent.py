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

from ..foundry import env, get_credential, project_endpoint
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


def run(stream: EventStream, payload: dict) -> None:
    endpoint = project_endpoint()
    model = env("FOUNDRY_MODEL_DEPLOYMENT_NAME", "MODEL_DEPLOYMENT_NAME", default="gpt-4o")
    connection_id = env("A2A_PROJECT_CONNECTION_ID")
    if not connection_id:
        # Simulate A2A behavior so the demo stays usable when no external A2A
        # connection is configured. This streams token deltas to mimic a
        # secondary agent response.
        stream.foundry("A2A connection", "(simulated)", kind="connection")
        stream.status("Simulating Agent A → Agent B interaction (no A2A connection)", kind="step")
        message = (payload or {}).get("message") or "What can the secondary agent do?"
        stream.user(message)
        sample = (
            "The secondary agent can fetch records, call APIs, and return structured "
            "data. This is a simulated streamed response for demo purposes."
        )
        for token in sample.split():
            stream.token(token + " ")
        stream.emit("token_done", {})
        stream.status("Simulation complete (A2A not configured).", kind="ok")
        return

    if not endpoint:
        stream.error("PROJECT_ENDPOINT is not set — run infra/provision first.")
        return

    try:
        from azure.ai.projects import AIProjectClient
        from azure.ai.projects.models import PromptAgentDefinition, A2ATool
    except ImportError as e:
        # A2ATool not available in this SDK version; fall back to simulation
        stream.status(f"A2A tool unavailable ({e.__class__.__name__}); using simulation", kind="warn")
        stream.foundry("A2A connection", "(simulated)", kind="connection")
        stream.status("Simulating Agent A → Agent B interaction", kind="step")
        message = (payload or {}).get("message") or "What can the secondary agent do?"
        stream.user(message)
        sample = (
            "The secondary agent can fetch records, call APIs, and return structured "
            "data. This is a simulated streamed response for demo purposes."
        )
        for token in sample.split():
            stream.token(token + " ")
        stream.emit("token_done", {})
        stream.status("Simulation complete (tool unavailable).", kind="ok")
        return

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
