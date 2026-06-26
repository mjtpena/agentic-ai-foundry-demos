#!/usr/bin/env python3
"""
Day 2 · Demo 12 (extended) — an Agent Framework agent that USES TOOLS
=====================================================================
The slide's joker shows the primitives; this companion shows the next step the
slides describe (slides 80-87: AIAgent + AgentThread + AIFunction tools): wrap
plain Python functions as tools and let the agent decide when to call them, with
a persistent AgentThread so memory carries across turns.

This is the "beyond the slide" piece — same framework, real tool-use + memory.

Prereqs:
  pip install agent-framework azure-identity python-dotenv
  az login
"""
from __future__ import annotations
import asyncio
import os
import sys
from pathlib import Path
from typing import Annotated

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.console import load_env, env, banner, rule, user_says, BOLD, RESET

from agent_framework import ai_function
from agent_framework.azure import AzureOpenAIChatClient
from azure.identity import AzureCliCredential


@ai_function
def convert_currency(
    amount: Annotated[float, "Amount to convert"],
    rate: Annotated[float, "Exchange rate to multiply by"],
) -> str:
    """Convert an amount using a provided exchange rate (local, deterministic tool)."""
    return f"{amount} × {rate} = {round(amount * rate, 2)}"


@ai_function
def packing_tip(destination: Annotated[str, "Destination city or region"]) -> str:
    """Return a one-line packing tip for a destination."""
    tips = {
        "reykjavik": "Layers + a waterproof shell; weather flips hourly.",
        "dubai": "Light, breathable clothing and strong sun protection.",
        "tokyo": "Comfortable walking shoes; compact umbrella in the rainy season.",
    }
    return tips.get(destination.strip().lower(), f"Pack for variable conditions in {destination}.")


async def main_async() -> None:
    endpoint = env("FOUNDRY_ACCOUNT_ENDPOINT", required=True)
    deployment = env("MODEL_DEPLOYMENT_NAME", default="gpt-4o")
    os.environ.setdefault("AZURE_OPENAI_ENDPOINT", endpoint)

    agent = AzureOpenAIChatClient(
        credential=AzureCliCredential(), endpoint=endpoint, deployment_name=deployment,
    ).create_agent(
        instructions="You are a concise travel assistant. Use tools when helpful.",
        name="TravelHelper",
        tools=[convert_currency, packing_tip],
    )

    # A persistent thread keeps context across the two turns (slide 89: AgentThread).
    thread = agent.get_new_thread()

    turn1 = "I'm flying to Reykjavik. What should I pack, and what is 250 USD in EUR if the rate is 0.92?"
    user_says(turn1)
    r1 = await agent.run(turn1, thread=thread)
    print(f"{BOLD}TravelHelper ▸{RESET} {r1.text}")

    turn2 = "Great — and how about for that same trip, any tip you'd add?"
    user_says(turn2)
    r2 = await agent.run(turn2, thread=thread)
    print(f"{BOLD}TravelHelper ▸{RESET} {r2.text}")
    rule("The 2nd turn resolved 'that same trip' from thread memory + reused tools.", "ok")


def main() -> None:
    load_env()
    banner("Day 2 · Demo 12 (extended) — Agent Framework with tools + memory",
            "ai_function tools · AgentThread memory · tool selection")
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
