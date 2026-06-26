#!/usr/bin/env python3
"""
Day 2 · Demo 7 — Connect to an OpenAPI Specification  (slide 30)
================================================================
Creates a Foundry prompt agent with an **OpenAPI 3.0 tool**. The agent reads the
local `assets/weather_openapi.json` spec, then calls the live wttr.in weather API
(anonymous auth) to answer "What's the weather in Seattle?".

Faithful to the slide's complete example. Enhancements: a real, working OpenAPI
spec for wttr.in (so it actually returns live weather), an environment
pre-flight check (the slide's "verify your environment" snippet), CLI city
argument, and guaranteed version cleanup.

The slide also shows key-based and managed-identity auth variants — those are
included verbatim below as reference dictionaries (`openapi_key_auth_tool`,
`openapi_mi_auth_tool`) so the full slide content is preserved.

Slide source:
  https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/openapi

Prereqs:
  pip install "azure-ai-projects" jsonref python-dotenv azure-identity
  az login
Env: AZURE_AI_PROJECT_ENDPOINT, AZURE_AI_MODEL_DEPLOYMENT_NAME
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

import jsonref

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.console import load_env, env, banner, rule, user_says, agent_says

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition

SPEC_PATH = Path(__file__).resolve().parent / "assets" / "weather_openapi.json"


def preflight(endpoint: str) -> None:
    """Slide's 'verify your environment is configured correctly' check."""
    with DefaultAzureCredential() as credential, \
         AIProjectClient(endpoint=endpoint, credential=credential) as project_client:
        _ = project_client  # touching the client validates auth + endpoint
    rule("Successfully connected to project", "ok")


def run(city: str) -> None:
    endpoint = env("AZURE_AI_PROJECT_ENDPOINT", "PROJECT_ENDPOINT", required=True)
    model = env("AZURE_AI_MODEL_DEPLOYMENT_NAME", "MODEL_DEPLOYMENT_NAME", default="gpt-4o")

    preflight(endpoint)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=endpoint, credential=credential) as project_client,
        project_client.get_openai_client() as openai_client,
    ):
        with open(SPEC_PATH, "r") as f:
            openapi_weather = jsonref.loads(f.read())

        # Anonymous-auth OpenAPI tool (slide).
        weather_tool = {
            "type": "openapi",
            "openapi": {
                "name": "weather",
                "spec": openapi_weather,
                "auth": {"type": "anonymous"},
            },
        }

        rule(f"Creating agent with OpenAPI 'weather' tool on model '{model}'", "step")
        agent = project_client.agents.create_version(
            agent_name="day2-openapi-agent",
            definition=PromptAgentDefinition(
                model=model,
                instructions=(
                    "You are a helpful weather assistant. Use the weather tool to look "
                    "up live conditions, then summarize temperature, sky, humidity and "
                    "wind in one friendly sentence."
                ),
                tools=[weather_tool],
            ),
            description="Weather assistant backed by an OpenAPI tool.",
        )
        rule(f"Agent created (id: {agent.id}, name: {agent.name}, version: {agent.version})", "ok")

        question = f"What's the weather in {city}?"
        user_says(question)
        response = openai_client.responses.create(
            input=question,
            extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
        )
        agent_says(response.output_text)

        rule("Cleaning up…", "step")
        project_client.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
        rule("Agent deleted", "ok")


# ---------------------------------------------------------------------------
# Reference only (from the slide): the other two auth schemes OpenAPI supports.
# Swap these in place of `weather_tool` when your API needs them.
# ---------------------------------------------------------------------------
def _reference_auth_variants(SPEC_NAME, TOOL_NAME="weather"):  # pragma: no cover
    openapi_key_auth_tool = {
        "type": "openapi",
        "openapi": {
            "name": TOOL_NAME,
            "spec": SPEC_NAME,
            "auth": {
                "type": "project_connection",
                "security_scheme": {
                    "project_connection_id": "/subscriptions/{{subscriptionID}}/resourceGroups/{{resourceGroupName}}/providers/Microsoft.CognitiveServices/accounts/{{foundryAccountName}}/projects/{{foundryProjectName}}/connections/{{foundryConnectionName}}"
                },
            },
        },
    }
    openapi_mi_auth_tool = {
        "type": "openapi",
        "openapi": {
            "name": TOOL_NAME,
            "description": "",
            "spec": SPEC_NAME,
            "auth": {
                "type": "managed_identity",
                "security_scheme": {"audience": "https://ai.azure.com"},
            },
        },
    }
    return openapi_key_auth_tool, openapi_mi_auth_tool


def main() -> None:
    parser = argparse.ArgumentParser(description="OpenAPI tool agent (Day 2 #7)")
    parser.add_argument("city", nargs="?", default="Seattle", help="city to fetch weather for")
    args = parser.parse_args()
    load_env()
    banner("Day 2 · Demo 7 — Connect to an OpenAPI Specification",
            "Foundry agent + OpenAPI 3.0 tool · live wttr.in weather · anonymous auth")
    run(args.city)


if __name__ == "__main__":
    main()
