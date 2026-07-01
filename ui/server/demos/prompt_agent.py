"""Day 1 · Demo 3 — Prompt agent with multi-turn memory (slide 84)."""
from __future__ import annotations

from ..foundry import env, get_credential, project_endpoint
from ..sse import EventStream

AGENT_NAME = "day1-prompt-agent"
INSTRUCTIONS = (
    "You are a concise, helpful assistant for a Microsoft Foundry workshop. "
    "Answer general-knowledge questions accurately. When a follow-up question "
    "depends on an earlier answer, use the conversation history rather than "
    "asking the user to repeat themselves."
)


def _clients():
    from azure.ai.projects import AIProjectClient

    endpoint = project_endpoint()
    if not endpoint:
        raise RuntimeError("PROJECT_ENDPOINT is not set — run infra/provision first.")
    project = AIProjectClient(endpoint=endpoint, credential=get_credential())
    return project, project.get_openai_client()


def _ensure_agent(stream: EventStream, project, model: str):
    from azure.ai.projects.models import PromptAgentDefinition

    stream.status(f"Creating prompt agent '{AGENT_NAME}' on {model}", kind="step")
    agent = project.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(model=model, instructions=INSTRUCTIONS),
    )
    stream.foundry("Agent version", f"{agent.name} · v{agent.version}", kind="agent",
                   id=agent.id, model=model)
    return agent


def _ask(stream: EventStream, openai, conversation_id: str, prompt: str) -> None:
    stream.user(prompt)
    response = openai.responses.create(
        conversation=conversation_id,
        extra_body={"agent_reference": {"name": AGENT_NAME, "type": "agent_reference"}},
        input=prompt,
    )
    stream.answer(response.output_text)
    usage = getattr(response, "usage", None)
    total = getattr(usage, "total_tokens", None) if usage else None
    if total is not None:
        stream.metric("Tokens", total)


def run(stream: EventStream, payload: dict) -> None:
    default_model = env("PROMPT_AGENT_MODEL", "MODEL_DEPLOYMENT_NAME", default="gpt-4o")
    model = inference.valid_agentservice_model((payload or {}).get("model") or default_model)
    mode = (payload or {}).get("mode", "scripted")
    project, openai = _clients()
    try:
        _ensure_agent(stream, project, model)
        if mode == "chat":
            conversation_id = (payload or {}).get("conversation_id")
            if not conversation_id:
                conv = openai.conversations.create()
                conversation_id = conv.id
                stream.foundry("Conversation", conversation_id, kind="conversation")
                stream.emit("conversation", {"id": conversation_id})
            message = (payload or {}).get("message", "").strip()
            if not message:
                stream.error("Type a message to send.")
                return
            _ask(stream, openai, conversation_id, message)
        else:
            conv = openai.conversations.create()
            stream.foundry("Conversation", conv.id, kind="conversation")
            stream.emit("conversation", {"id": conv.id})
            stream.status("Scripted multi-turn memory test", kind="step")
            _ask(stream, openai, conv.id, "What is the size of France in square miles?")
            _ask(stream, openai, conv.id, "And what is the capital city?")
            stream.status(
                "The 2nd question never says 'France' — it resolved from conversation "
                "memory. ✓ Memory works.", kind="ok")
    finally:
        for c in (openai, project):
            try:
                c.close()
            except Exception:
                pass
