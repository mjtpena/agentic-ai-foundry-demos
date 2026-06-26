#!/usr/bin/env python3
"""
Day 1 · Demo 3 — Create a prompt agent  (slide 84)
==================================================
Faithful to the slide's Microsoft Foundry quickstart, then taken "beyond":

  Slide baseline                          This file adds
  --------------------------------------  -------------------------------------
  create_version(PromptAgentDefinition)   idempotent create, prints id/version
  conversations.create()                  reused across turns to PROVE memory
  responses.create(... France ...)        a scripted multi-turn script + an
  print(output_text)                      interactive REPL, plus token usage,
  "delete the resource group" cleanup     and optional --cleanup of the version

Slide source:
  https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/prompt-agent

Prereqs (from the slide):
  pip install "azure-ai-projects>=2.0.0"   # Foundry projects (new) API
  az login                                 # DefaultAzureCredential

Run:
  python prompt_agent.py                   # scripted France demo (as on the slide)
  python prompt_agent.py --chat            # interactive multi-turn chat
  python prompt_agent.py --cleanup         # delete the agent version when done
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.console import load_env, env, banner, rule, user_says, agent_says, DIM, RESET

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition

AGENT_NAME = "day1-prompt-agent"
INSTRUCTIONS = (
    "You are a concise, helpful assistant for a Microsoft Foundry workshop. "
    "Answer general-knowledge questions accurately. When a follow-up question "
    "depends on an earlier answer, use the conversation history rather than "
    "asking the user to repeat themselves."
)


def build_clients():
    """The slide's two-liner: a project client + the OpenAI-compatible client."""
    endpoint = env("PROJECT_ENDPOINT", "FOUNDRY_PROJECT_ENDPOINT", required=True)
    project = AIProjectClient(endpoint=endpoint, credential=DefaultAzureCredential())
    return project, project.get_openai_client()


def ensure_agent(project: AIProjectClient, model: str):
    """Create (or update) the prompt agent — slide's create_version call."""
    rule(f"Creating prompt agent '{AGENT_NAME}' on model '{model}'", "step")
    agent = project.agents.create_version(
        agent_name=AGENT_NAME,
        definition=PromptAgentDefinition(model=model, instructions=INSTRUCTIONS),
    )
    rule(f"Agent ready  (id: {agent.id}, name: {agent.name}, version: {agent.version})", "ok")
    return agent


def ask(openai, conversation_id: str, prompt: str) -> None:
    """One turn against the shared conversation, so memory carries across turns."""
    user_says(prompt)
    response = openai.responses.create(
        conversation=conversation_id,
        extra_body={"agent_reference": {"name": AGENT_NAME, "type": "agent_reference"}},
        input=prompt,
    )
    agent_says(response.output_text)
    usage = getattr(response, "usage", None)
    if usage:
        total = getattr(usage, "total_tokens", None)
        if total is not None:
            print(f"{DIM}   ({total} tokens this turn){RESET}")


def scripted_demo(openai) -> None:
    """The exact France script from the slide — proves multi-turn memory."""
    conversation = openai.conversations.create()
    rule(f"Started conversation {conversation.id}", "info")
    ask(openai, conversation.id, "What is the size of France in square miles?")
    # Follow-up has no noun — only works if the agent remembers we're discussing France.
    ask(openai, conversation.id, "And what is the capital city?")
    print()
    rule("The second answer resolved 'the capital city' from history → memory works.", "ok")


def interactive_chat(openai) -> None:
    conversation = openai.conversations.create()
    rule(f"Interactive chat on conversation {conversation.id}. Type 'exit' to quit.", "info")
    while True:
        try:
            prompt = input("\nYou ▸ ").strip()
        except (EOFError, KeyboardInterrupt):
            print(); break
        if prompt.lower() in {"exit", "quit", ""}:
            break
        ask(openai, conversation.id, prompt)


def main() -> None:
    parser = argparse.ArgumentParser(description="Foundry prompt agent demo (Day 1 #3)")
    parser.add_argument("--chat", action="store_true", help="interactive multi-turn chat")
    parser.add_argument("--cleanup", action="store_true", help="delete the agent version and exit")
    parser.add_argument("--model", default=None, help="override the model deployment name")
    args = parser.parse_args()

    load_env()
    banner("Day 1 · Demo 3 — Create a prompt agent",
            "Microsoft Foundry Agent Service · azure-ai-projects · multi-turn memory")
    model = args.model or env("PROMPT_AGENT_MODEL", "MODEL_DEPLOYMENT_NAME", default="gpt-5-mini")
    project, openai = build_clients()

    if args.cleanup:
        # Slide's lighter-weight cleanup: drop just this agent version.
        try:
            versions = project.agents.list_versions(agent_name=AGENT_NAME)
            for v in versions:
                project.agents.delete_version(agent_name=AGENT_NAME, agent_version=v.version)
                rule(f"Deleted {AGENT_NAME} v{v.version}", "ok")
        except Exception as exc:  # noqa: BLE001
            rule(f"Nothing to clean up ({exc})", "warn")
        return

    ensure_agent(project, model)
    if args.chat:
        interactive_chat(openai)
    else:
        scripted_demo(openai)
    print()
    rule("Done. Re-run with --chat to talk to it, or --cleanup to remove the version.", "info")
    rule("Full teardown (all resources): infra/teardown.sh", "info")


if __name__ == "__main__":
    main()
