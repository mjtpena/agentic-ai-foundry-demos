#!/usr/bin/env python3
"""
Day 1 · Demo 4 — Deploy your first hosted agent  (slides 86-87)
===============================================================
A *code-based* (hosted) agent: you write the orchestration in Python and Foundry
runs it on **Agent Service**. This file defines the agent with the Microsoft
Agent Framework's Foundry client (`agent_framework.foundry.FoundryChatClient`),
which executes the agent on Foundry Agent Service via your project endpoint —
the tools below run server-side as part of the agent's run, and the SAME code
deploys to the cloud with `azd deploy`, no rewrite.

Faithful to the slide's `get_local_date_time` example, extended with a second
local tool so the agent must *choose between* tools (real tool-use, not a single
canned call).

Run it standalone:
    python agent.py            # one-shot demo against Foundry Agent Service
"""
from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

from agent_framework._tools import ai_function
from agent_framework.foundry import FoundryChatClient
from azure.identity import DefaultAzureCredential

PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT") or os.getenv("FOUNDRY_PROJECT_ENDPOINT")
DEFAULT_MODEL = os.getenv("HOSTED_AGENT_MODEL") or os.getenv("MODEL_DEPLOYMENT_NAME") or "gpt-4.1"

INSTRUCTIONS = (
    "You are a helpful assistant that can tell users the current date and time in "
    "any location and how long until a given hour there. When a user asks about "
    "time in a city, map it to the correct IANA timezone and use the appropriate "
    "tool. Be concise."
)


@ai_function
def get_local_date_time(iana_timezone: str) -> str:
    """Get the current date and time for a given timezone.

    A LOCAL Python function that runs server-side as part of the hosted agent —
    demonstrating how code-based agents execute custom logic that prompt agents
    cannot access.

    Args:
        iana_timezone: IANA timezone string, e.g. "Asia/Tokyo", "Europe/London".
    """
    try:
        now = datetime.now(ZoneInfo(iana_timezone))
        return f"The current date and time in {iana_timezone} is " + now.strftime(
            "%A, %B %d, %Y at %I:%M %p %Z"
        )
    except Exception as e:  # noqa: BLE001
        return f"Error: unable to get time for timezone '{iana_timezone}'. {e}"


@ai_function
def hours_until(iana_timezone: str, target_hour_24: int) -> str:
    """Compute how many hours remain until a target hour (0-23) in a timezone.

    A second local tool so the agent must *reason about which tool to call*,
    showing genuine tool selection rather than a single hard-wired call.

    Args:
        iana_timezone: IANA timezone string, e.g. "Asia/Tokyo".
        target_hour_24: Hour of day in 24h form, 0-23.
    """
    try:
        now = datetime.now(ZoneInfo(iana_timezone))
        target = now.replace(hour=int(target_hour_24) % 24, minute=0, second=0, microsecond=0)
        delta_h = (target - now).total_seconds() / 3600
        if delta_h < 0:
            delta_h += 24
        return f"About {delta_h:.1f} hours until {int(target_hour_24):02d}:00 in {iana_timezone}."
    except Exception as e:  # noqa: BLE001
        return f"Error: {e}"


def build_agent(model: str | None = None):
    """Create the code-based agent on Foundry Agent Service (project endpoint).

    FoundryChatClient runs the agent on Foundry Agent Service — the tools execute
    server-side during the agent's run.
    """
    client = FoundryChatClient(
        project_endpoint=PROJECT_ENDPOINT,
        model=model or DEFAULT_MODEL,
        credential=DefaultAzureCredential(),
    )
    return client.as_agent(
        name="day1-hosted-agent",
        instructions=INSTRUCTIONS,
        tools=[get_local_date_time, hours_until],
    )


async def ask(message: str, model: str | None = None) -> str:
    """Run the hosted agent for one message and return its answer text."""
    agent = build_agent(model)
    result = await agent.run(message)
    return result.text or ""


if __name__ == "__main__":
    import asyncio

    print(asyncio.run(ask("What time is it in Tokyo, and how long until 6pm there?")))
