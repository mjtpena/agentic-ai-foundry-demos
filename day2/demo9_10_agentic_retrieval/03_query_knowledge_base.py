#!/usr/bin/env python3
"""
Day 2 · Demos 9 & 10 — Step 3: Query the knowledge base  (slides 56, 61)
=======================================================================
Calls the **retrieve** action on `earth-at-night-kb` with the exact multi-part
question from the slide. Agentic retrieval decomposes it into subqueries, runs
them in parallel, semantically ranks, and returns a synthesized, citation-backed
answer plus the activity/reference debug data.

Mirrors slide 56's retrieve call and slide 61's portal test query.
Slide source:
  https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-how-to-retrieve
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.console import load_env, env, banner, rule, user_says, agent_says, DIM, RESET

from azure.identity import DefaultAzureCredential

QUERY = (
    "Why do suburban belts display larger December brightening than urban cores even "
    "though absolute light levels are higher downtown? Why is the Phoenix nighttime "
    "street grid so sharply visible from space, whereas large stretches of the "
    "interstate between midwestern cities remain comparatively dim?"
)
SYSTEM = (
    "You can answer questions about the Earth at night. Sources have a JSON format with "
    "a ref_id that must be cited in the answer. If you do not have the answer, respond "
    "with 'I do not know'."
)


def main() -> None:
    load_env()
    banner("Day 2 · Demos 9-10 · Step 3 — Query the knowledge base",
            "retrieve action · parallel subqueries · citation-backed answer")
    endpoint = env("SEARCH_ENDPOINT", "AZURE_SEARCH_ENDPOINT", required=True)
    kb_name = env("KNOWLEDGE_BASE_NAME", default="earth-at-night-kb")
    cred = DefaultAzureCredential()

    try:
        from azure.search.documents.knowledgebases import KnowledgeBaseRetrievalClient
        from azure.search.documents.knowledgebases.models import (
            KnowledgeBaseRetrievalRequest, KnowledgeBaseMessage, KnowledgeBaseMessageTextContent,
        )
    except ImportError:
        rule("KnowledgeBaseRetrievalClient not in your azure-search-documents build.", "error")
        rule("Install the preview pinned in requirements.txt, or use portal_runbook.md.", "warn")
        return

    kb_client = KnowledgeBaseRetrievalClient(endpoint=endpoint, knowledge_base_name=kb_name, credential=cred)

    request = KnowledgeBaseRetrievalRequest(messages=[
        KnowledgeBaseMessage(role="assistant", content=[KnowledgeBaseMessageTextContent(text=SYSTEM)]),
        KnowledgeBaseMessage(role="user", content=[KnowledgeBaseMessageTextContent(text=QUERY)]),
    ])

    user_says(QUERY)
    rule("Retrieving (planning + parallel subqueries + semantic rank)…", "step")
    result = kb_client.retrieve(request)

    answer = result.response[0].content[0].text
    agent_says(answer)

    activity = getattr(result, "activity", None)
    if activity:
        print(f"\n{DIM}--- Activity (query plan / subqueries) ---{RESET}")
        for step in activity:
            print(f"   {getattr(step, 'type', step)}")


if __name__ == "__main__":
    main()
