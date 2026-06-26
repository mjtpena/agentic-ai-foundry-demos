"""Static metadata for every demo — drives the UI nav, headers and badges.

`id` matches the route segment (/api/demos/<id>/run) and the frontend renderer.
"""
from __future__ import annotations

CATALOG = [
    {
        "id": "prompt-agent",
        "day": 1,
        "number": 3,
        "slide": 84,
        "title": "Prompt Agent",
        "capability": "Multi-turn memory",
        "summary": "A Foundry prompt agent that remembers earlier turns — the second "
                   "question never names France, yet it answers about France.",
        "foundry": ["Foundry Agent Service", "azure-ai-projects", "Conversations"],
        "services": ["agent", "model", "conversation"],
        "status": "ready",
    },
    {
        "id": "hosted-agent",
        "day": 1,
        "number": 4,
        "slide": 87,
        "title": "Hosted Agent",
        "capability": "Code-based agent + local tools",
        "summary": "A code-based agent whose Python tools run server-side. Runs locally "
                   "on :8088 via azd, then deploys to Foundry Agent Service unchanged.",
        "foundry": ["Hosted Agents", "agent-framework", "azd"],
        "services": ["agent", "model", "tools", "hosting"],
        "status": "gated",
    },
    {
        "id": "mcp-tools",
        "day": 2,
        "number": 6,
        "slide": 27,
        "title": "MCP Tools",
        "capability": "Live tool-use over MCP",
        "summary": "An agent connected to the public Microsoft Learn Docs MCP server, "
                   "answering from Microsoft's latest official docs.",
        "foundry": ["Foundry Agent Service", "azure-ai-agents", "MCP"],
        "services": ["agent", "model", "mcp", "tools"],
        "status": "ready",
    },
    {
        "id": "openapi-tool",
        "day": 2,
        "number": 7,
        "slide": 30,
        "title": "OpenAPI Tool",
        "capability": "Call any REST API from a spec",
        "summary": "A prompt agent given an OpenAPI 3.0 spec, calling the live wttr.in "
                   "weather API to answer real questions.",
        "foundry": ["Foundry Agent Service", "OpenAPI tool", "azure-ai-projects"],
        "services": ["agent", "model", "openapi", "tools"],
        "status": "ready",
    },
    {
        "id": "a2a-agent",
        "day": 2,
        "number": 8,
        "slide": 35,
        "title": "A2A Agent",
        "capability": "Agent-to-agent calls",
        "summary": "Agent A calls a secondary A2A-compatible agent through a project "
                   "connection and summarizes its answer — keeping control of the turn.",
        "foundry": ["Foundry Agent Service", "A2A tool", "Project connections"],
        "services": ["agent", "model", "a2a", "connection"],
        "status": "gated",
    },
    {
        "id": "agentic-retrieval",
        "day": 2,
        "number": 910,
        "slide": 61,
        "title": "Agentic Retrieval",
        "capability": "Query planning + grounded citations",
        "summary": "Azure AI Search decomposes a multi-part question into parallel "
                   "subqueries, semantically ranks, and returns a citation-backed answer.",
        "foundry": ["Azure AI Search", "Knowledge base", "Semantic ranker"],
        "services": ["search", "knowledge", "embedding"],
        "status": "setup",
    },
    {
        "id": "agent-framework",
        "day": 2,
        "number": 12,
        "slide": 83,
        "title": "Agent Framework",
        "capability": "Streaming · tools · memory",
        "summary": "Microsoft Agent Framework: streamed responses, Python ai_function "
                   "tools the agent chooses, and AgentThread memory across turns.",
        "foundry": ["agent-framework", "Azure OpenAI", "AIFunction tools"],
        "services": ["model", "tools", "memory", "streaming"],
        "status": "ready",
    },
    {
        "id": "guardrails",
        "day": 3,
        "number": 16,
        "slide": 49,
        "title": "Guardrails",
        "capability": "Content safety + prompt shields",
        "summary": "Azure AI Content Safety scores harm categories, matches a custom "
                   "blocklist, and detects prompt-injection — the engine behind Foundry guardrails.",
        "foundry": ["Azure AI Content Safety", "Blocklists", "Prompt Shields"],
        "services": ["contentsafety", "blocklist", "promptshield"],
        "status": "ready",
    },
]

BY_ID = {d["id"]: d for d in CATALOG}


def demo_number_label(d: dict) -> str:
    n = d["number"]
    return "9 & 10" if n == 910 else str(n)
