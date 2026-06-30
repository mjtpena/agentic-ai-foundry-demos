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
        "status": "ready",
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
        "status": "ready",
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
    {
        "id": "evaluations",
        "day": 3,
        "number": 17,
        "slide": 40,
        "title": "Evaluations",
        "capability": "Quality + safety scorecard",
        "summary": "Foundry's two evaluator families over a dataset of agent answers: "
                   "model-as-judge quality (1–5) and Content Safety risk scores (0–7). "
                   "A planted hallucination and unsafe answer get caught.",
        "foundry": ["azure-ai-evaluation", "Quality evaluators", "Risk & safety"],
        "services": ["evaluation", "model", "contentsafety"],
        "status": "ready",
    },
    {
        "id": "red-team",
        "day": 3,
        "number": 18,
        "slide": 41,
        "title": "AI Red Teaming",
        "capability": "Automated adversarial scan",
        "summary": "The AI Red Teaming Agent fires attack objectives × PyRIT-style "
                   "strategies (Base64, leetspeak, ROT13) at the live model and reports "
                   "an Attack Success Rate scorecard. Low ASR = strong guardrails.",
        "foundry": ["azure-ai-evaluation", "RedTeam", "Content Safety"],
        "services": ["redteam", "model", "contentsafety"],
        "status": "ready",
    },
    {
        "id": "tracing",
        "day": 3,
        "number": 19,
        "slide": 16,
        "title": "Observability",
        "capability": "OpenTelemetry agent traces",
        "summary": "A multi-step agent turn (plan → tool → answer) traced with "
                   "OpenTelemetry — spans, durations and token usage — the same data the "
                   "Control Plane Observability pane reads from Application Insights.",
        "foundry": ["OpenTelemetry", "Azure Monitor", "Control Plane"],
        "services": ["tracing", "model", "tools"],
        "status": "ready",
    },
    {
        "id": "entra-agent-id",
        "day": 3,
        "number": 20,
        "slide": 45,
        "title": "Entra Agent ID",
        "capability": "Keyless identity + RBAC",
        "summary": "Secure agents with Microsoft Entra: acquire a keyless token, decode "
                   "its claims (who the agent is), and list the RBAC role assignments "
                   "(what it may do) — least privilege, fully auditable.",
        "foundry": ["Microsoft Entra ID", "Managed identity", "Azure RBAC"],
        "services": ["entra", "rbac", "identity"],
        "status": "ready",
    },
    {
        "id": "advanced-guardrails",
        "day": 3,
        "number": 21,
        "slide": 49,
        "title": "Advanced Guardrails",
        "capability": "Output + boundary protection",
        "summary": "Beyond input moderation: indirect prompt injection (XPIA) in retrieved "
                   "docs, protected-material detection (text & code), groundedness, and PII "
                   "redaction — the output-side guardrails for enterprise agents.",
        "foundry": ["Prompt Shields (XPIA)", "Protected material", "PII (Language)"],
        "services": ["contentsafety", "promptshield", "pii"],
        "status": "ready",
    },
]

BY_ID = {d["id"]: d for d in CATALOG}

# Assign a per-day demo number (1-based within each day) so the UI shows clean
# "Day 2 · Demo 3" labels instead of the confusing global sequence
# (…, 6, 7, 8, 9 & 10, 12, 16). Numbering follows CATALOG declaration order — the
# intended teaching order — rather than the raw `number`, whose 910 sentinel
# ("9 & 10") would otherwise sort after 12. Mutates CATALOG in place so the value
# is included in the /api/demos payload.
_per_day_count: dict[int, int] = {}
for _d in CATALOG:
    _per_day_count[_d["day"]] = _per_day_count.get(_d["day"], 0) + 1
    _d["day_number"] = _per_day_count[_d["day"]]


def demo_number_label(d: dict) -> str:
    """Per-day demo label, e.g. '3' for Day 2 · Demo 3."""
    return str(d.get("day_number") or d["number"])
