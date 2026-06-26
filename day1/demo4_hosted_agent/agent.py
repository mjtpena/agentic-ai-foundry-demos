#!/usr/bin/env python3
"""
Day 1 · Demo 4 — Deploy your first hosted agent  (slides 86-87)
===============================================================
A *code-based* (hosted) agent: you write the orchestration, Foundry runs it as a
container on Agent Service. The hosting adapter (`from_agent_framework`) exposes
the agent as the Foundry Responses API on localhost:8088 for local testing,
then `azd deploy` ships the same code to the cloud — no rewrite.

Faithful to the slide's `get_local_date_time` example, extended with a second
local tool so the demo shows the agent *choosing between* tools (real tool-use,
not a single canned call).

Slide source:
  https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/hosted-agents
  https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/quickstart-hosted-agent

Local loop (see setup.sh / README):
  azd ai agent run                         # starts THIS file on :8088
  azd ai agent invoke --local "What time is it in Tokyo?"
"""
from __future__ import annotations
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv(override=True)

from agent_framework import ai_function, ChatAgent
from agent_framework.azure import AzureAIAgentClient
from azure.ai.agentserver.agentframework import from_agent_framework
from azure.identity import DefaultAzureCredential

PROJECT_ENDPOINT = os.getenv("PROJECT_ENDPOINT") or os.getenv("FOUNDRY_PROJECT_ENDPOINT")
MODEL_DEPLOYMENT_NAME = os.getenv("HOSTED_AGENT_MODEL", os.getenv("MODEL_DEPLOYMENT_NAME", "gpt-4.1"))


@ai_function
def get_local_date_time(iana_timezone: str) -> str:
    """Get the current date and time for a given timezone.

    A LOCAL Python function that runs on the server — demonstrating how code-based
    agents can execute custom logic that prompt agents cannot access.

    Args:
        iana_timezone: IANA timezone string, e.g. "America/Los_Angeles",
            "America/New_York", "Europe/London", "Asia/Tokyo".
    """
    try:
        tz = ZoneInfo(iana_timezone)
        now = datetime.now(tz)
        return f"The current date and time in {iana_timezone} is {now.strftime('%A, %B %d, %Y at %I:%M %p %Z')}"
    except Exception as e:  # noqa: BLE001
        return f"Error: Unable to get time for timezone '{iana_timezone}'. {e}"


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
        target = now.replace(hour=target_hour_24 % 24, minute=0, second=0, microsecond=0)
        delta_h = (target - now).total_seconds() / 3600
        if delta_h < 0:
            delta_h += 24
        return f"About {delta_h:.1f} hours until {target_hour_24:02d}:00 in {iana_timezone}."
    except Exception as e:  # noqa: BLE001
        return f"Error: {e}"


# Create the agent with two local Python tools.
agent = ChatAgent(
    chat_client=AzureAIAgentClient(
        project_endpoint=PROJECT_ENDPOINT,
        model_deployment_name=MODEL_DEPLOYMENT_NAME,
        credential=DefaultAzureCredential(),
    ),
    instructions=(
        "You are a helpful assistant that can tell users the current date and "
        "time in any location and how long until a given hour there. When a user "
        "asks about time in a city, map it to the correct IANA timezone and use "
        "the appropriate tool."
    ),
    tools=[get_local_date_time, hours_until],
)

if __name__ == "__main__":
    # Wrap with the hosting adapter and start the local web server (:8088).
    from_agent_framework(agent).run()
