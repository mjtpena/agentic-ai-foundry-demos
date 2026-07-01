"""Demo 12 — Microsoft Agent Framework: streaming, tools, memory (slide 83).

Adapted to the installed agent-framework 1.9.x surface:
  • Foundry model endpoint client = OpenAIChatCompletionClient(azure_endpoint=…, credential=…)
  • agent            = client.as_agent(instructions=…, name=…, tools=[…])
  • streaming        = agent.run(text, stream=True)  -> async chunks with .text
  • memory           = an AgentSession passed to agent.run(…, session=session)
  • tools            = @ai_function-decorated Python functions
"""
from __future__ import annotations

import asyncio
from typing import Annotated

from ..foundry import account_endpoint, env, selected_model
from ..sse import EventStream

API_VERSION = "2024-10-21"


def run(stream: EventStream, payload: dict) -> None:
    payload = payload or {}
    # "joker" (plain streaming) runs model-switchable through the unified Azure AI
    # inference client; "tools" stays on the Agent Framework (the framework's
    # ai_function tools + AgentSession memory are its showcase, on Azure OpenAI).
    if payload.get("mode") == "tools":
        asyncio.run(_run_async(stream, payload))
    else:
        _joker_inference(stream, payload)


def _joker_inference(stream: EventStream, payload: dict) -> None:
    from azure.ai.inference.models import SystemMessage, UserMessage

    model = inference.valid_model(payload.get("model"))
    message = payload.get("message") or "Tell me a joke about a pirate."
    stream.foundry("Model", inference.label_for(model), kind="model")
    stream.foundry("Agent", "Joker", kind="agent")
    stream.user(message)
    stream.status(f"Streaming tokens from {inference.label_for(model)} via Azure AI inference…", kind="step")
    for chunk in inference.stream_text(
        model, [SystemMessage(content="You are good at telling jokes."), UserMessage(content=message)]
    ):
        stream.token(chunk)
    stream.emit("token_done", {})


async def _run_async(stream: EventStream, payload: dict) -> None:
    from agent_framework.openai import OpenAIChatCompletionClient
    from agent_framework._tools import ai_function
    from azure.identity import DefaultAzureCredential

    endpoint = account_endpoint()
    if not endpoint:
        stream.error("FOUNDRY_ACCOUNT_ENDPOINT is not set — run infra/provision first.")
        return
    deployment = selected_model(payload, "MODEL_DEPLOYMENT_NAME", "AZURE_AI_MODEL_DEPLOYMENT_NAME", default="gpt-4.1-mini")
    api_version = env("AZURE_OPENAI_API_VERSION", default=API_VERSION)
    mode = payload.get("mode", "joker")

    client = OpenAIChatCompletionClient(
        azure_endpoint=endpoint, credential=DefaultAzureCredential(),
        api_version=api_version, model=deployment,
    )
    stream.foundry("Foundry model endpoint", deployment, kind="model", endpoint=endpoint)

    if mode == "tools":
        await _tools_demo(stream, client, ai_function, payload)
    else:
        await _joker_demo(stream, client, payload)


async def _joker_demo(stream: EventStream, client, payload: dict) -> None:
    agent = client.as_agent(instructions="You are good at telling jokes.", name="Joker")
    stream.foundry("Agent", "Joker", kind="agent")
    message = payload.get("message") or "Tell me a joke about a pirate."
    stream.user(message)
    stream.status("agent.run(stream=True) — streaming tokens from the agent", kind="step")
    async for update in agent.run(message, stream=True):
        if getattr(update, "text", None):
            stream.token(update.text)
    stream.emit("token_done", {})


async def _tools_demo(stream: EventStream, client, ai_function, payload: dict) -> None:
    @ai_function
    def convert_currency(
        amount: Annotated[float, "Amount to convert"],
        rate: Annotated[float, "Exchange rate to multiply by"],
    ) -> str:
        """Convert an amount using a provided exchange rate."""
        return f"{amount} × {rate} = {round(amount * rate, 2)}"

    @ai_function
    def packing_tip(destination: Annotated[str, "Destination city or region"]) -> str:
        """Return a one-line packing tip for a destination."""
        tips = {
            "reykjavik": "Layers + a waterproof shell; weather flips hourly.",
            "dubai": "Light, breathable clothing and strong sun protection.",
            "tokyo": "Comfortable walking shoes; compact umbrella in the rainy season.",
        }
        return tips.get(destination.strip().lower(),
                        f"Pack for variable conditions in {destination}.")

    agent = client.as_agent(
        instructions="You are a concise travel assistant. Use tools when helpful.",
        name="TravelHelper", tools=[convert_currency, packing_tip],
    )
    stream.foundry("Agent", "TravelHelper", kind="agent")
    stream.foundry("Tools", "convert_currency, packing_tip", kind="toolcall")

    from agent_framework import AgentSession
    session = AgentSession()

    turn1 = payload.get("message") or (
        "I'm flying to Reykjavik. What should I pack, and what is 250 USD in EUR "
        "if the rate is 0.92?")
    stream.user(turn1)
    stream.status("Turn 1 — agent selects tools", kind="step")
    r1 = await agent.run(turn1, session=session)
    stream.answer(r1.text)

    turn2 = "Great — and how about for that same trip, any tip you'd add?"
    stream.user(turn2)
    stream.status("Turn 2 — reusing AgentSession memory", kind="step")
    r2 = await agent.run(turn2, session=session)
    stream.answer(r2.text)
    stream.status("The 2nd turn resolved 'that same trip' from session memory. ✓", kind="ok")
