"""Day 2 · Demo 7 — Connect to an OpenAPI specification (slide 30)."""
from __future__ import annotations

from .. import inference
from ..foundry import REPO_ROOT, env, get_credential
from ..sse import EventStream

SPEC_PATH = REPO_ROOT / "day2" / "demo7_openapi_tool" / "assets" / "weather_openapi.json"
INSTRUCTIONS = (
    "You are a helpful weather assistant. Use the weather tool to look up live "
    "conditions, then summarize temperature, sky, humidity and wind in one "
    "friendly sentence."
)


def run(stream: EventStream, payload: dict) -> None:
    import jsonref
    from azure.ai.projects import AIProjectClient
    from azure.ai.projects.models import PromptAgentDefinition

    endpoint = env("AZURE_AI_PROJECT_ENDPOINT", "PROJECT_ENDPOINT")
    if not endpoint:
        stream.error("PROJECT_ENDPOINT is not set — run infra/provision first.")
        return
    default_model = env("AZURE_AI_MODEL_DEPLOYMENT_NAME", "MODEL_DEPLOYMENT_NAME", default="gpt-4o")
    model = inference.valid_agentservice_model((payload or {}).get("model") or default_model)
    city = (payload or {}).get("city") or "Seattle"

    project = AIProjectClient(endpoint=endpoint, credential=get_credential())
    openai_client = project.get_openai_client()
    try:
        stream.status("Connected to the Foundry project", kind="ok")
        spec = jsonref.loads(SPEC_PATH.read_text())
        weather_tool = {
            "type": "openapi",
            "openapi": {"name": "weather", "spec": spec, "auth": {"type": "anonymous"}},
        }
        stream.foundry("OpenAPI tool", "weather → wttr.in (anonymous auth)", kind="openapi")

        stream.status(f"Creating agent with the OpenAPI tool on {model}", kind="step")
        agent = project.agents.create_version(
            agent_name="day2-openapi-agent",
            definition=PromptAgentDefinition(model=model, instructions=INSTRUCTIONS, tools=[weather_tool]),
            description="Weather assistant backed by an OpenAPI tool.",
        )
        stream.foundry("Agent version", f"{agent.name} · v{agent.version}", kind="agent", id=agent.id)

        question = f"What's the weather in {city}?"
        stream.user(question)
        stream.status("Agent is calling the live weather API…", kind="step")
        response = openai_client.responses.create(
            input=question,
            extra_body={"agent_reference": {"name": agent.name, "type": "agent_reference"}},
        )
        stream.answer(response.output_text)

        project.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
        stream.status("Agent version deleted (cleanup)", kind="ok")
    finally:
        for c in (openai_client, project):
            try:
                c.close()
            except Exception:
                pass
