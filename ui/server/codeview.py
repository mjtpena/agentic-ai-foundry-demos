"""'Code behind' for each demo — the real wrapper source, syntax-highlighted,
with the Microsoft Foundry SDK lines given a subtle accent.

Highlighting is done by a small, self-contained Python tokenizer (regex based,
no third-party dependency) so the View Source panel always renders proper IDE
style colours — even if Pygments isn't installed. Lines that touch the Foundry
SDK get a thin left accent; the Foundry identifiers themselves are coloured in
the brand tone. Everything else is the harness that streams results to the UI.
"""
from __future__ import annotations

import re

from .foundry import REPO_ROOT

# Map each demo to the source worth showing. For the hosted agent and A2A agent
# we show the REAL agent definition (the Foundry SDK code that runs the agent),
# not the console's thin invoker wrapper.
DEMO_SOURCES = {
    "prompt-agent": "ui/server/demos/prompt_agent.py",
    "hosted-agent": "day1/demo4_hosted_agent/agent.py",
    "mcp-tools": "ui/server/demos/mcp_tools.py",
    "openapi-tool": "ui/server/demos/openapi_tool.py",
    "a2a-agent": "day2/demo8_a2a_agent/a2a_agent.py",
    "agentic-retrieval": "ui/server/demos/agentic_retrieval.py",
    "agent-framework": "ui/server/demos/agent_framework.py",
    "guardrails": "ui/server/demos/guardrails.py",
    # Day 3 governance/security demos — View Source shows the real, slide-faithful
    # Foundry-SDK standalone scripts (the console runs always-on variants).
    "evaluations": "day3/demo17_evaluations/evaluate_agent.py",
    "red-team": "day3/demo18_red_team/run_red_team.py",
    "tracing": "day3/demo19_observability/trace_agent.py",
    "entra-agent-id": "day3/demo20_entra_agent_id/inspect_identity.py",
    "advanced-guardrails": "day3/demo21_advanced_guardrails/advanced_guardrails.py",
}

# Foundry SDK identifiers — coloured at the token level and used to flag lines.
FOUNDRY_IDENTS = [
    # azure-ai-projects (Microsoft Foundry projects + prompt agents)
    "AIProjectClient", "PromptAgentDefinition", "A2ATool", "get_openai_client",
    "create_version", "delete_version", "list_versions",
    # azure-ai-agents (Foundry Agent Service)
    "AgentsClient", "McpTool", "ToolSet", "create_agent", "create_and_process",
    "run_steps", "ListSortOrder", "delete_agent",
    # azure-ai-contentsafety (Foundry guardrails engine)
    "ContentSafetyClient", "BlocklistClient", "analyze_text", "AnalyzeTextOptions",
    "TextBlocklist", "TextBlocklistItem", "AddOrUpdateTextBlocklistItemsOptions",
    "shield_prompt", "ShieldPromptOptions", "TextCategory",
    # azure-search-documents (Azure AI Search + agentic retrieval)
    "SearchIndexClient", "SearchClient", "KnowledgeBase", "KnowledgeSourceReference",
    "SearchIndexKnowledgeSource", "KnowledgeBaseRetrievalClient",
    "KnowledgeBaseRetrievalRequest", "KnowledgeBaseAzureOpenAIModel",
    "AzureOpenAIVectorizer", "SemanticSearch", "KnowledgeRetrievalOutputMode",
    "create_or_update_knowledge_base", "create_or_update_knowledge_source",
    "create_or_update_index", "retrieve",
    # Microsoft Agent Framework + Foundry Agent Service (hosted agents)
    "OpenAIChatCompletionClient", "ai_function", "AgentSession", "as_agent", "run_stream",
    "FoundryChatClient", "FoundryAgent", "ChatAgent", "build_agent", "from_agent_framework",
    "A2AAgent", "AzureAIAgentClient",
    # Entra ID credentials
    "DefaultAzureCredential", "AzureCliCredential", "ManagedIdentityCredential",
    "get_bearer_token_provider",
    # azure-ai-evaluation (Foundry evaluations + AI Red Teaming Agent)
    "GroundednessEvaluator", "RelevanceEvaluator", "CoherenceEvaluator",
    "FluencyEvaluator", "ViolenceEvaluator", "HateUnfairnessEvaluator",
    "SexualEvaluator", "SelfHarmEvaluator", "evaluate",
    "RedTeam", "RiskCategory", "AttackStrategy",
    # OpenTelemetry tracing (Foundry observability)
    "TracerProvider", "InMemorySpanExporter", "ConsoleSpanExporter",
    "SimpleSpanProcessor", "configure_azure_monitor", "start_as_current_span",
    "get_tracer", "set_tracer_provider",
]
_FOUNDRY_IDENT_SET = frozenset(FOUNDRY_IDENTS)

# Substrings that also flag a whole line as Foundry (import paths + agent reference).
FOUNDRY_LINE_MARKERS = FOUNDRY_IDENTS + [
    "azure.ai.projects", "azure.ai.agents", "azure.ai.contentsafety",
    "azure.search.documents", "agent_framework", "agent_reference",
    "azure.ai.evaluation", "azure.monitor.opentelemetry", "opentelemetry",
]


def get_code(demo_id: str) -> dict | None:
    rel = DEMO_SOURCES.get(demo_id)
    if not rel:
        return None
    try:
        src = (REPO_ROOT / rel).read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        return {"filename": rel, "html": "", "raw": "", "symbols": [],
                "foundry_lines": 0, "error": str(exc)}
    lines = src.splitlines()
    hl = [i + 1 for i, ln in enumerate(lines) if any(m in ln for m in FOUNDRY_LINE_MARKERS)]
    symbols = [s for s in FOUNDRY_IDENTS if re.search(r"\b" + re.escape(s) + r"\b", src)]
    return {
        "filename": rel,
        "html": _highlight(src, hl),
        "raw": src,
        "symbols": symbols,
        "foundry_lines": len(hl),
    }


# --------------------------------------------------------------------------- #
# Self-contained Python syntax highlighter
# --------------------------------------------------------------------------- #
_PY_KEYWORDS = frozenset((
    "False", "None", "True", "and", "as", "assert", "async", "await", "break",
    "class", "continue", "def", "del", "elif", "else", "except", "finally",
    "for", "from", "global", "if", "import", "in", "is", "lambda", "nonlocal",
    "not", "or", "pass", "raise", "return", "try", "while", "with", "yield",
    "match", "case",
))
_PY_BUILTINS = frozenset((
    "print", "len", "range", "dict", "list", "tuple", "set", "frozenset", "str",
    "int", "float", "bool", "bytes", "open", "isinstance", "issubclass", "hasattr",
    "getattr", "setattr", "super", "enumerate", "zip", "min", "max", "sum", "any",
    "all", "sorted", "reversed", "type", "object", "property", "staticmethod",
    "classmethod", "format", "repr", "map", "filter", "next", "iter", "vars",
    "Exception", "ValueError", "TypeError", "KeyError", "RuntimeError",
))

_TOKEN_RE = re.compile(
    r"""
      (?P<comment>\#[^\n]*)
    | (?P<string>(?i:[rbfu]{0,3})(?:'''[\s\S]*?'''|\"\"\"[\s\S]*?\"\"\"|'(?:\\.|[^'\\\n])*'|"(?:\\.|[^"\\\n])*"))
    | (?P<decorator>@[ \t]*[A-Za-z_][A-Za-z0-9_.]*)
    | (?P<number>(?:0[xXoObB][0-9a-fA-F_]+)|(?:\d[\d_]*\.?\d*(?:[eE][+-]?\d+)?[jJ]?))
    | (?P<name>[A-Za-z_][A-Za-z0-9_]*)
    | (?P<nl>\n)
    | (?P<ws>[ \t]+)
    | (?P<op>[+\-*/%=<>!&|^~@:,.;?\\()\[\]{}])
    | (?P<other>.)
    """,
    re.VERBOSE,
)


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _tokenize_lines(src: str) -> list[str]:
    """Return a list of HTML strings, one per source line (token spans applied)."""
    lines: list[list[str]] = [[]]
    prev_sig: str | None = None  # previous significant token (skips whitespace)

    def push(frag: str) -> None:
        lines[-1].append(frag)

    def push_text(text: str, cls: str | None) -> None:
        # Split on newlines so every rendered line is self-contained (matters for
        # triple-quoted strings that span lines).
        parts = text.split("\n")
        for i, part in enumerate(parts):
            if i > 0:
                lines.append([])
            if not part:
                continue
            esc = _esc(part)
            push(f'<span class="cv-{cls}">{esc}</span>' if cls else esc)

    for m in _TOKEN_RE.finditer(src):
        kind = m.lastgroup
        text = m.group()
        if kind == "nl":
            lines.append([])
        elif kind in ("ws", "other"):
            push(_esc(text))
        elif kind == "comment":
            push_text(text, "c")
        elif kind == "string":
            push_text(text, "s")
        elif kind == "number":
            push_text(text, "m")
            prev_sig = text
        elif kind == "decorator":
            push_text(text, "decorator")
            prev_sig = text
        elif kind == "op":
            push(f'<span class="cv-o">{_esc(text)}</span>')
            prev_sig = text
        elif kind == "name":
            if text in _PY_KEYWORDS:
                cls = "k"
            elif text in _FOUNDRY_IDENT_SET:
                cls = "fdry"
            elif prev_sig == "def":
                cls = "nf"
            elif prev_sig == "class":
                cls = "nc"
            elif text in ("self", "cls"):
                cls = "bp"
            elif text in _PY_BUILTINS:
                cls = "nb"
            else:
                cls = None
            push_text(text, cls)
            prev_sig = text
        else:  # pragma: no cover - defensive
            push(_esc(text))

    # A trailing newline produces one extra empty line vs. str.splitlines(); drop it
    # so line numbers line up with the Foundry-line markers computed by get_code().
    if len(lines) > 1 and not lines[-1] and src.endswith("\n"):
        lines.pop()
    return ["".join(frags) for frags in lines]


def _highlight(src: str, hl_lines: list[int]) -> str:
    rendered = _tokenize_lines(src)
    flagged = set(hl_lines)
    out = ['<div class="hlcode"><table class="cv"><tbody>']
    for i, code in enumerate(rendered, start=1):
        cls = "cv-line fdry-line" if i in flagged else "cv-line"
        out.append(
            f'<tr class="{cls}"><td class="cv-gutter">{i}</td>'
            f'<td class="cv-code">{code or "&nbsp;"}</td></tr>'
        )
    out.append("</tbody></table></div>")
    return "".join(out)
