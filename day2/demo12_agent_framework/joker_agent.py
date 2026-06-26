#!/usr/bin/env python3
"""
Day 2 · Demo 12 — Create and run an agent with Agent Framework  (slide 83)
==========================================================================
The Microsoft Agent Framework "hello world": create an agent on Azure OpenAI
Chat Completions and run it three ways the slide shows —
  1. plain run()                 -> single response
  2. run_stream()                -> token-by-token streaming
  3. run(ChatMessage(... image)) -> multimodal (text + image) input

Auth uses AzureCliCredential, exactly as the slide's prerequisites specify
(`az login`, with Cognitive Services OpenAI User role).

Slide source:
  https://learn.microsoft.com/en-us/agent-framework/tutorials/agents/run-agent

Prereqs:
  pip install agent-framework azure-identity python-dotenv
  az login        # AzureCliCredential
Env: FOUNDRY_ACCOUNT_ENDPOINT (Azure OpenAI endpoint), MODEL_DEPLOYMENT_NAME
"""
from __future__ import annotations
import argparse
import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.console import load_env, env, banner, rule, user_says, GREEN, RESET, BOLD

from agent_framework import ChatMessage, TextContent, UriContent, Role
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential


def make_agent():
    """Slide: create a chat client + agent. We pass the Azure OpenAI endpoint
    and deployment from .env so it works against the provisioned Foundry account."""
    endpoint = env("FOUNDRY_ACCOUNT_ENDPOINT", required=True)
    deployment = env("MODEL_DEPLOYMENT_NAME", "AZURE_AI_MODEL_DEPLOYMENT_NAME", default="gpt-4o")
    os.environ.setdefault("AZURE_OPENAI_ENDPOINT", endpoint)
    return AzureOpenAIChatClient(
        credential=AzureCliCredential(),
        endpoint=endpoint,
        deployment_name=deployment,
    ).create_agent(
        instructions="You are good at telling jokes.",
        name="Joker",
    )


async def demo_plain(agent) -> None:
    rule("1) run() — single response", "step")
    user_says("Tell me a joke about a pirate.")
    result = await agent.run("Tell me a joke about a pirate.")
    print(f"{BOLD}Joker ▸{RESET} {result.text}")


async def demo_stream(agent) -> None:
    rule("2) run_stream() — streaming tokens", "step")
    user_says("Tell me a joke about a pirate.")
    print(f"{BOLD}Joker ▸{RESET} ", end="", flush=True)
    async for update in agent.run_stream("Tell me a joke about a pirate."):
        if update.text:
            print(f"{GREEN}{update.text}{RESET}", end="", flush=True)
    print()


async def demo_multimodal(agent, image_url: str) -> None:
    rule("3) run(ChatMessage) — multimodal text + image", "step")
    message = ChatMessage(role=Role.USER, contents=[
        TextContent(text="Tell me a joke about this image?"),
        UriContent(uri=image_url, media_type="image/jpeg"),
    ])
    user_says(f"[image] {image_url}  +  'Tell me a joke about this image?'")
    result = await agent.run(message)
    print(f"{BOLD}Joker ▸{RESET} {result.text}")


async def main_async(args) -> None:
    agent = make_agent()
    await demo_plain(agent)
    print()
    await demo_stream(agent)
    if args.image:
        print()
        await demo_multimodal(agent, args.image)


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent Framework joker (Day 2 #12)")
    parser.add_argument("--image", default="https://samplesite.org/clown.jpg",
                        help="image URL for the multimodal turn (set empty to skip)")
    args = parser.parse_args()
    load_env()
    banner("Day 2 · Demo 12 — Create and run an agent with Agent Framework",
            "agent-framework · AzureOpenAIChatClient · run / run_stream / multimodal")
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
