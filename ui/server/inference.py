"""Unified, multi-publisher model inference for the demo console.

Every chat model deployed on the Foundry account — OpenAI *and* non-OpenAI
(Meta Llama, Mistral, Microsoft Phi, …) — is reachable through ONE endpoint, the
Azure AI model-inference route `{FOUNDRY_ACCOUNT_ENDPOINT}/models`, with the same
managed-identity auth. This module wraps `azure-ai-inference` so the demos can be
switched between models just by passing a `model` deployment name.

Validated live (2026-06-29): gpt-4o, Llama-3.3-70B-Instruct, Mistral-Large-3 all
chat and tool-call through this path; Phi-4-mini chats (no tools).
"""
from __future__ import annotations

import threading

from .foundry import env

# Curated registry of models DEPLOYED on the account. `tools` = reliable
# function-calling. Override the visible set with the DEMO_CHAT_MODELS app
# setting (comma-separated deployment names) if you add/remove deployments.
_REGISTRY = [
    {"id": "gpt-4o",                 "label": "GPT-4o",         "publisher": "OpenAI",     "tools": True},
    {"id": "gpt-4.1",                "label": "GPT-4.1",        "publisher": "OpenAI",     "tools": True},
    {"id": "gpt-4.1-mini",           "label": "GPT-4.1 mini",   "publisher": "OpenAI",     "tools": True},
    # Llama does single tool calls fine, but Azure serverless rejects the *parallel*
    # tool calls it emits for multi-tool tasks, so it's flagged non-tool here (it
    # stays available for plain-chat demos: A2A Agent B, agent-framework joker).
    {"id": "Llama-3.3-70B-Instruct", "label": "Llama 3.3 70B",  "publisher": "Meta",       "tools": False},
    {"id": "Mistral-Large-3",        "label": "Mistral Large 3","publisher": "Mistral AI", "tools": True},
    {"id": "Phi-4-mini-instruct",    "label": "Phi-4 mini",     "publisher": "Microsoft",  "tools": False},
]

DEFAULT_MODEL = "gpt-4o"
_TOKEN_SCOPE = "https://cognitiveservices.azure.com/.default"
_API_VERSION = "2024-05-01-preview"

_client = None
_lock = threading.Lock()


def list_models(tools_only: bool = False) -> list[dict]:
    allow = env("DEMO_CHAT_MODELS")
    models = _REGISTRY
    if allow:
        ids = {x.strip() for x in allow.split(",") if x.strip()}
        models = [m for m in _REGISTRY if m["id"] in ids]
    if tools_only:
        models = [m for m in models if m["tools"]]
    return [dict(m) for m in models]


def valid_model(model: str | None, tools_required: bool = False) -> str:
    """Return `model` if it's a known (and tool-capable, if required) deployment,
    else the default — so a bad/empty payload never breaks a demo."""
    ids = {m["id"] for m in list_models(tools_only=tools_required)}
    return model if (model and model in ids) else DEFAULT_MODEL


def agentservice_models() -> list[dict]:
    """Models usable by Foundry Agent Service (the hosted-agent / prompt-agent
    runtime) — currently the OpenAI-family deployments on the account."""
    return [m for m in list_models() if m["publisher"] == "OpenAI"]


def valid_agentservice_model(model: str | None) -> str:
    ids = {m["id"] for m in agentservice_models()}
    return model if (model and model in ids) else DEFAULT_MODEL


def label_for(model: str) -> str:
    for m in _REGISTRY:
        if m["id"] == model:
            return m["label"]
    return model


def get_client():
    """Cached ChatCompletionsClient against the account's /models route."""
    global _client
    with _lock:
        if _client is not None:
            return _client
        from azure.ai.inference import ChatCompletionsClient
        from azure.identity import DefaultAzureCredential

        base = (env("FOUNDRY_ACCOUNT_ENDPOINT") or "").rstrip("/")
        if not base:
            raise RuntimeError("FOUNDRY_ACCOUNT_ENDPOINT is not set")
        endpoint = base if base.endswith("/models") else base + "/models"
        _client = ChatCompletionsClient(
            endpoint=endpoint,
            credential=DefaultAzureCredential(),
            credential_scopes=[_TOKEN_SCOPE],
            api_version=_API_VERSION,
        )
        return _client


def complete(model: str, messages, tools=None, tool_choice=None, max_tokens: int | None = None):
    """Non-streaming completion. `messages`/`tools` are azure-ai-inference objects."""
    kwargs = {"messages": messages, "model": model}
    if tools:
        kwargs["tools"] = tools
        if tool_choice:
            kwargs["tool_choice"] = tool_choice
    if max_tokens:
        kwargs["max_tokens"] = max_tokens
    return get_client().complete(**kwargs)


def stream_text(model: str, messages):
    """Yield content deltas (str) as they stream from the model."""
    for update in get_client().complete(messages=messages, model=model, stream=True):
        if update.choices:
            delta = update.choices[0].delta
            if delta and delta.content:
                yield delta.content
