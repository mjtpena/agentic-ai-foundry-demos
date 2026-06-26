#!/usr/bin/env python3
"""
Day 2 · Demos 9 & 10 — Step 2: Create a knowledge base  (slides 54-55)
=====================================================================
Creates the `earth-at-night-kb` **knowledge base** that drives agentic
retrieval: it points at the `earth-at-night-ks` knowledge source and an LLM
deployment, with **answer synthesis** enabled so responses come back as
citation-backed natural language (slide 55).

Mirrors slide 54's `KnowledgeBase` with low reasoning effort + answer synthesis.

Run after 01_create_knowledge_source.py.
Slide source:
  https://learn.microsoft.com/en-us/azure/search/agentic-retrieval-how-to-create-knowledge-base
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.console import load_env, env, banner, rule

from azure.identity import DefaultAzureCredential
from azure.search.documents.indexes import SearchIndexClient


def main() -> None:
    load_env()
    banner("Day 2 · Demos 9-10 · Step 2 — Create a knowledge base",
            "Azure AI Search · answer synthesis · low reasoning effort")
    endpoint = env("SEARCH_ENDPOINT", "AZURE_SEARCH_ENDPOINT", required=True)
    foundry_endpoint = env("FOUNDRY_ACCOUNT_ENDPOINT", required=True)
    kb_name = env("KNOWLEDGE_BASE_NAME", default="earth-at-night-kb")
    ks_name = env("KNOWLEDGE_SOURCE_NAME", default="earth-at-night-ks")
    chat_deploy = env("MODEL_DEPLOYMENT_NAME", default="gpt-4o")

    cred = DefaultAzureCredential()
    index_client = SearchIndexClient(endpoint, cred)

    try:
        from azure.search.documents.indexes.models import (
            KnowledgeBase, KnowledgeSourceReference,
            KnowledgeRetrievalLowReasoningEffort, KnowledgeRetrievalOutputMode,
            KnowledgeBaseAzureOpenAIModel, AzureOpenAIVectorizerParameters,
        )
    except ImportError:
        rule("Your azure-search-documents build lacks KnowledgeBase models.", "error")
        rule("Install the preview pinned in requirements.txt, or use portal_runbook.md.", "warn")
        return

    # LLM the knowledge base uses for query planning + answer synthesis.
    model = KnowledgeBaseAzureOpenAIModel(
        azure_open_ai_parameters=AzureOpenAIVectorizerParameters(
            resource_url=foundry_endpoint, deployment_name=chat_deploy, model_name=chat_deploy,
        )
    )

    knowledge_base = KnowledgeBase(
        name=kb_name,
        knowledge_sources=[KnowledgeSourceReference(name=ks_name)],
        retrieval_reasoning_effort=KnowledgeRetrievalLowReasoningEffort(),
        output_mode=KnowledgeRetrievalOutputMode.ANSWER_SYNTHESIS,
        models=[model],
    )
    index_client.create_or_update_knowledge_base(knowledge_base)
    rule(f"Knowledge base '{kb_name}' created/updated successfully", "ok")
    rule("Next: python 03_query_knowledge_base.py", "info")


if __name__ == "__main__":
    main()
