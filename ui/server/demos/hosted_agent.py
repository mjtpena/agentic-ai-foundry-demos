"""Day 1 · Demo 4 — Hosted Agent (invoker).

This is a thin invoker. The REAL hosted agent is defined in
day1/demo4_hosted_agent/agent.py and runs on **Foundry Agent Service** via the
Microsoft Agent Framework's FoundryChatClient (its Python tools execute
server-side during the agent's run). View source shows that agent definition,
not this wrapper.
"""
from __future__ import annotations

import asyncio
import importlib.util

from .. import inference
from ..foundry import REPO_ROOT
from ..sse import EventStream

_AGENT_PATH = REPO_ROOT / "day1" / "demo4_hosted_agent" / "agent.py"
_agent_mod = None


def _load_agent():
    """Load the canonical hosted-agent definition (day1/demo4_hosted_agent/agent.py)."""
    global _agent_mod
    if _agent_mod is None:
        spec = importlib.util.spec_from_file_location("day1_hosted_agent_def", _AGENT_PATH)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _agent_mod = mod
    return _agent_mod


def status() -> dict:
    return {"ready": True, "mode": "foundry-agent-service"}


def run(stream: EventStream, payload: dict) -> None:
    payload = payload or {}
    message = payload.get("message") or "What time is it in Tokyo, and how long until 6pm there?"
    # Foundry Agent Service runs the OpenAI-family deployments.
    model = inference.valid_agentservice_model(payload.get("model"))

    stream.foundry("Foundry Agent Service", "code-based agent · project endpoint", kind="hosting")
    stream.foundry("Model", inference.label_for(model), kind="model")
    stream.foundry("Server-side tools", "get_local_date_time, hours_until", kind="toolcall")
    stream.user(message)
    stream.status(
        f"Running the code-based agent on Foundry Agent Service ({inference.label_for(model)})…",
        kind="step",
    )
    try:
        mod = _load_agent()
        answer = asyncio.run(mod.ask(message, model))
        stream.answer(answer or "(no output)")
        stream.status("Hosted agent responded · the same code deploys to Foundry with `azd deploy`.", kind="ok")
    except Exception as exc:  # noqa: BLE001
        stream.error(
            f"Hosted agent call failed: {exc}",
            hint="Ensure the app's managed identity can access the Foundry project and the "
                 "selected model deployment (Azure AI User / Cognitive Services OpenAI User).",
        )
