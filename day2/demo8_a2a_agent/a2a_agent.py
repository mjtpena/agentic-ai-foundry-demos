#!/usr/bin/env python3
"""
Day 2 · Demo 8 — Add an A2A agent endpoint to Foundry Agent Service  (slide 35, preview)
========================================================================================
Adds an **Agent-to-Agent (A2A)** tool to a Foundry prompt agent. Agent A (this
one) calls a secondary A2A-compatible agent through a project connection, then
summarizes the answer for the user — Agent A keeps control of the conversation
(the slide's "A2A tool vs. multi-agent workflow" distinction).

Faithful to the slide's streaming sample, with the full event handling
(`response.created`, text deltas, `remote_function_call`, completion) intact and
an env pre-flight that fails fast with a clear message if the A2A connection
isn't set yet.

Setup the connection first:
  ./setup_a2a_connection.sh                  # creates the A2A project connection
  # then copy the printed connection id into ../../.env as A2A_PROJECT_CONNECTION_ID

Slide source:
  https://learn.microsoft.com/en-us/azure/ai-foundry/agents/how-to/tools/agent-to-agent

Prereqs:
  pip install "azure-ai-projects[agents]" python-dotenv azure-identity
  az login
Env: FOUNDRY_PROJECT_ENDPOINT, FOUNDRY_MODEL_DEPLOYMENT_NAME, A2A_PROJECT_CONNECTION_ID
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.console import load_env, env, banner, rule, user_says, GREEN, RESET, BOLD

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
try:
    # A2ATool ships in azure-ai-projects[agents] PRERELEASE (see slide prereqs).
    from azure.ai.projects.models import A2ATool
except ImportError as _e:
    raise SystemExit(
        'This demo needs the prerelease azure-ai-projects[agents] (A2ATool). Install with:\n'
        '  pip install --pre "azure-ai-projects[agents]"\n'
        f"(import error: {_e})"
    )


def run() -> None:
    endpoint = env("FOUNDRY_PROJECT_ENDPOINT", "PROJECT_ENDPOINT", required=True)
    model = env("FOUNDRY_MODEL_DEPLOYMENT_NAME", "MODEL_DEPLOYMENT_NAME", default="gpt-4o")
    connection_id = env("A2A_PROJECT_CONNECTION_ID", required=True)

    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=endpoint, credential=credential) as project_client,
        project_client.get_openai_client() as openai_client,
    ):
        tool = A2ATool(project_connection_id=connection_id)

        rule(f"Creating agent with A2A tool (connection: …{connection_id[-24:]})", "step")
        agent = project_client.agents.create_version(
            agent_name="day2-a2a-agent",
            definition=PromptAgentDefinition(
                model=model,
                instructions="You are a helpful assistant. When a question is better "
                             "answered by the connected secondary agent, call it and "
                             "summarize its response for the user.",
                tools=[tool],
            ),
        )
        rule(f"Agent created (id: {agent.id}, name: {agent.name}, version: {agent.version})", "ok")

        user_input = input("\nEnter your question (e.g., 'What can the secondary agent do?'):\n> ")
        user_says(user_input)

        stream_response = openai_client.responses.create(
            stream=True,
            tool_choice="required",
            input=user_input,
            extra_body={"agent": {"name": agent.name, "type": "agent_reference"}},
        )

        print(f"\n{BOLD}Agent ▸{RESET} ", end="", flush=True)
        for event in stream_response:
            if event.type == "response.created":
                rule(f"\nFollow-up response created with ID: {event.response.id}", "info")
            elif event.type == "response.output_text.delta":
                print(f"{GREEN}{event.delta}{RESET}", end="", flush=True)
            elif event.type == "response.text.done":
                print()
                rule("Follow-up response done!", "ok")
            elif event.type == "response.output_item.done":
                item = event.item
                if item.type == "remote_function_call":
                    print(f"   Call ID: {getattr(item, 'call_id', None)}")
                    print(f"   Label: {getattr(item, 'label', None)}")
            elif event.type == "response.completed":
                rule("Follow-up completed!", "ok")
                print(f"\nFull response: {event.response.output_text}")

        rule("Cleaning up…", "step")
        project_client.agents.delete_version(agent_name=agent.name, agent_version=agent.version)
        rule("Agent deleted", "ok")


def main() -> None:
    load_env()
    banner("Day 2 · Demo 8 — A2A agent endpoint (preview)",
            "Foundry agent + A2ATool · streaming · Agent A keeps control")
    run()


if __name__ == "__main__":
    main()
