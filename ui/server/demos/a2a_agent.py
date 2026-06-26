"""Day 2 · Demo 8 — Add an A2A agent endpoint (slide 35, preview).

Gated: needs A2A_PROJECT_CONNECTION_ID (run day2/demo8_a2a_agent/setup_a2a_connection.sh
against a secondary A2A endpoint, then put the printed id in .env).
"""
from __future__ import annotations

from ..foundry import env, get_credential
from ..sse import EventStream


def status() -> dict:
    conn = env("A2A_PROJECT_CONNECTION_ID")
    return {
        "ready": bool(conn),
        "connection_id": conn,
        "reason": None if conn else "A2A_PROJECT_CONNECTION_ID not set",
    }


def run(stream: EventStream, payload: dict) -> None:
    endpoint = env("FOUNDRY_PROJECT_ENDPOINT", "PROJECT_ENDPOINT")
    model = env("FOUNDRY_MODEL_DEPLOYMENT_NAME", "MODEL_DEPLOYMENT_NAME", default="gpt-4o")
    connection_id = env("A2A_PROJECT_CONNECTION_ID")
    if not connection_id:
        stream.error(
            "No A2A connection configured.",
            hint="Run day2/demo8_a2a_agent/setup_a2a_connection.sh with A2A_TARGET_URL set, "
                 "then add A2A_PROJECT_CONNECTION_ID to .env.")
        return

    from azure.ai.projects import AIProjectClient
    from azure.ai.projects.models import PromptAgentDefinition, A2ATool

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

        message = (payload or {}).get("message") or "What can the secondary agent do?"
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
        project.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
        stream.status("Agent version deleted (cleanup)", kind="ok")
    finally:
        for c in (openai_client, project):
            try:
                c.close()
            except Exception:
                pass
