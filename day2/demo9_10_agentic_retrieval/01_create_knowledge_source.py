#!/usr/bin/env python3
"""
Day 2 · Demos 9 & 10 — Step 1: Create a knowledge source  (slides 51, 60-61)
============================================================================
Creates the `earth-at-night` search index, uploads the NASA "Earth at Night"
sample documents, and registers a **knowledge source** (`earth-at-night-ks`)
over that index — the reusable reference to source data that the knowledge base
queries during agentic retrieval.

Faithful to slide 51's `SearchIndexKnowledgeSource` with `SourceDataFields`
limited to human-readable fields (id, page_chunk, page_number) so citations stay
interpretable.

NOTE — preview SDK: agentic retrieval objects (KnowledgeSource / KnowledgeBase)
live in the azure-search-documents **preview**. Install the version pinned in
../../requirements.txt. Class names track the 2025-11-01-preview wave shown on
the slides; if your installed preview differs, see the quickstart link below.

Slide source:
  https://learn.microsoft.com/en-us/azure/search/search-get-started-agentic-retrieval

Run (in order):
  python 01_create_knowledge_source.py
  python 02_create_knowledge_base.py
  python 03_query_knowledge_base.py
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.console import load_env, env, banner, rule

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex, SearchField, SearchFieldDataType, SimpleField, SearchableField,
    VectorSearch, HnswAlgorithmConfiguration, VectorSearchProfile,
    AzureOpenAIVectorizer, AzureOpenAIVectorizerParameters,
    SemanticConfiguration, SemanticPrioritizedFields, SemanticField, SemanticSearch,
)


def get_clients():
    endpoint = env("SEARCH_ENDPOINT", "AZURE_SEARCH_ENDPOINT", required=True)
    cred = DefaultAzureCredential()
    return endpoint, cred, SearchIndexClient(endpoint, cred)


def create_index(index_client: SearchIndexClient, index_name: str, foundry_endpoint: str, embed_deploy: str) -> None:
    """Create a hybrid (text + vector) index with a semantic config + vectorizer."""
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        SearchableField(name="page_chunk", type=SearchFieldDataType.String),
        SimpleField(name="page_number", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
        SearchField(
            name="page_embedding_text_3_large",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            vector_search_dimensions=3072, vector_search_profile_name="hnsw-profile",
        ),
    ]
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
        profiles=[VectorSearchProfile(name="hnsw-profile", algorithm_configuration_name="hnsw", vectorizer_name="ks-vectorizer")],
        vectorizers=[AzureOpenAIVectorizer(
            vectorizer_name="ks-vectorizer",
            parameters=AzureOpenAIVectorizerParameters(
                resource_url=foundry_endpoint, deployment_name=embed_deploy, model_name="text-embedding-3-large",
            ),
        )],
    )
    semantic = SemanticSearch(configurations=[SemanticConfiguration(
        name="semantic-config",
        prioritized_fields=SemanticPrioritizedFields(content_fields=[SemanticField(field_name="page_chunk")]),
    )])
    index = SearchIndex(name=index_name, fields=fields, vector_search=vector_search, semantic_search=semantic)
    index_client.create_or_update_index(index)
    rule(f"Index '{index_name}' created/updated", "ok")


def upload_docs(endpoint, cred, index_name: str) -> None:
    sample = Path(__file__).resolve().parent / "sample_docs.json"
    if not sample.exists():
        rule("sample_docs.json not found — generating a tiny built-in sample.", "warn")
        docs = _builtin_sample()
    else:
        docs = json.loads(sample.read_text())
    sc = SearchClient(endpoint, index_name, cred)
    sc.upload_documents(documents=docs)
    rule(f"Uploaded {len(docs)} documents to '{index_name}'", "ok")


def create_knowledge_source(endpoint, cred, ks_name: str, index_name: str) -> None:
    """Slide 51 — SearchIndexKnowledgeSource with human-readable SourceDataFields."""
    try:
        from azure.search.documents.indexes.models import (
            SearchIndexKnowledgeSource, SearchIndexKnowledgeSourceParameters, SearchIndexFieldReference,
        )
    except ImportError:
        rule("Your azure-search-documents build lacks KnowledgeSource models.", "error")
        rule("Install the preview pinned in requirements.txt, or use the portal (see portal_runbook.md).", "warn")
        return
    index_client = SearchIndexClient(endpoint, cred)
    ks = SearchIndexKnowledgeSource(
        name=ks_name,
        search_index_parameters=SearchIndexKnowledgeSourceParameters(
            search_index_name=index_name,
            source_data_fields=[
                SearchIndexFieldReference(name="id"),
                SearchIndexFieldReference(name="page_chunk"),
                SearchIndexFieldReference(name="page_number"),
            ],
        ),
    )
    index_client.create_or_update_knowledge_source(knowledge_source=ks)
    rule(f"Knowledge source '{ks_name}' created/updated successfully", "ok")


def _builtin_sample():
    """A handful of Earth-at-Night style chunks so the demo works even offline."""
    return [
        {"id": "1", "page_number": 25, "page_chunk":
            "Suburban belts often show larger relative December brightening than urban "
            "cores. Urban cores are already near sensor saturation, so their percentage "
            "change is small, while lower-baseline suburbs can rise sharply."},
        {"id": "2", "page_number": 40, "page_chunk":
            "The Phoenix nighttime street grid is sharply visible from space because its "
            "regular, well-lit arterial layout reflects and emits light uniformly."},
        {"id": "3", "page_number": 41, "page_chunk":
            "Long interstate stretches between midwestern cities remain comparatively dim: "
            "lighting is sparse and intermittent away from population centers."},
        {"id": "4", "page_number": 12, "page_chunk":
            "The brightest lights are generally the most urbanized areas, but not "
            "necessarily the most populated; low-light regions can still hold large populations."},
    ]


def main() -> None:
    load_env()
    banner("Day 2 · Demos 9-10 · Step 1 — Create a knowledge source",
            "Azure AI Search · earth-at-night index + earth-at-night-ks")
    endpoint, cred, index_client = get_clients()
    index_name = env("SEARCH_INDEX_NAME", default="earth-at-night")
    ks_name = env("KNOWLEDGE_SOURCE_NAME", default="earth-at-night-ks")
    foundry_endpoint = env("FOUNDRY_ACCOUNT_ENDPOINT", required=True)
    embed_deploy = env("EMBEDDING_DEPLOYMENT", default="text-embedding-3-large")

    create_index(index_client, index_name, foundry_endpoint, embed_deploy)
    upload_docs(endpoint, cred, index_name)
    create_knowledge_source(endpoint, cred, ks_name, index_name)
    rule("Next: python 02_create_knowledge_base.py", "info")


if __name__ == "__main__":
    main()
