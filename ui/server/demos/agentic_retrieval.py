"""Day 2 · Demos 9 & 10 — Agentic retrieval (slides 51-61).

setup()  : create index + upload sample docs + knowledge source + knowledge base
run()    : retrieve — query planning, parallel subqueries, citation-backed answer
status() : whether the knowledge base already exists
"""
from __future__ import annotations

from ..foundry import env, get_credential
from ..sse import EventStream

DEFAULT_QUERY = (
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


def _names():
    return {
        "search_endpoint": env("SEARCH_ENDPOINT", "AZURE_SEARCH_ENDPOINT"),
        "foundry_endpoint": env("FOUNDRY_ACCOUNT_ENDPOINT"),
        "index": env("SEARCH_INDEX_NAME", default="earth-at-night"),
        "ks": env("KNOWLEDGE_SOURCE_NAME", default="earth-at-night-ks"),
        "kb": env("KNOWLEDGE_BASE_NAME", default="earth-at-night-kb"),
        "embed": env("EMBEDDING_DEPLOYMENT", default="text-embedding-3-large"),
        "chat": env("MODEL_DEPLOYMENT_NAME", default="gpt-4o"),
    }


def _builtin_sample():
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


def status() -> dict:
    n = _names()
    if not n["search_endpoint"]:
        return {"ready": False, "reason": "SEARCH_ENDPOINT not set"}
    try:
        from azure.search.documents.indexes import SearchIndexClient

        client = SearchIndexClient(n["search_endpoint"], get_credential())
        kbs = []
        try:
            kbs = [kb.name for kb in client.list_knowledge_bases()]
        except Exception:
            kbs = []
        return {"ready": n["kb"] in kbs, "kb": n["kb"], "knowledge_bases": kbs}
    except Exception as exc:  # noqa: BLE001
        return {"ready": False, "reason": f"{type(exc).__name__}: {exc}"}


def setup(stream: EventStream, payload: dict) -> None:
    from azure.search.documents import SearchClient
    from azure.search.documents.indexes import SearchIndexClient
    from azure.search.documents.indexes.models import (
        SearchIndex, SearchField, SearchFieldDataType, SimpleField, SearchableField,
        VectorSearch, HnswAlgorithmConfiguration, VectorSearchProfile,
        AzureOpenAIVectorizer, AzureOpenAIVectorizerParameters,
        SemanticConfiguration, SemanticPrioritizedFields, SemanticField, SemanticSearch,
    )

    n = _names()
    if not n["search_endpoint"] or not n["foundry_endpoint"]:
        stream.error("SEARCH_ENDPOINT / FOUNDRY_ACCOUNT_ENDPOINT not set.")
        return
    cred = get_credential()
    index_client = SearchIndexClient(n["search_endpoint"], cred)

    # 1) index
    stream.status(f"Creating hybrid index '{n['index']}' (text + vector + semantic)…", kind="step")
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True, filterable=True),
        SearchableField(name="page_chunk", type=SearchFieldDataType.String),
        SimpleField(name="page_number", type=SearchFieldDataType.Int32, filterable=True, sortable=True),
        SearchField(name="page_embedding_text_3_large",
                    type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                    vector_search_dimensions=3072, vector_search_profile_name="hnsw-profile"),
    ]
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
        profiles=[VectorSearchProfile(name="hnsw-profile", algorithm_configuration_name="hnsw",
                                      vectorizer_name="ks-vectorizer")],
        vectorizers=[AzureOpenAIVectorizer(
            vectorizer_name="ks-vectorizer",
            parameters=AzureOpenAIVectorizerParameters(
                resource_url=n["foundry_endpoint"], deployment_name=n["embed"],
                model_name="text-embedding-3-large"))],
    )
    semantic = SemanticSearch(configurations=[SemanticConfiguration(
        name="semantic-config",
        prioritized_fields=SemanticPrioritizedFields(
            content_fields=[SemanticField(field_name="page_chunk")]))])
    index_client.create_or_update_index(SearchIndex(
        name=n["index"], fields=fields, vector_search=vector_search, semantic_search=semantic))
    stream.foundry("Index", n["index"], kind="search")

    # 2) docs
    docs = _builtin_sample()
    SearchClient(n["search_endpoint"], n["index"], cred).upload_documents(documents=docs)
    stream.foundry("Documents uploaded", len(docs), kind="search")

    # 3) knowledge source
    stream.status(f"Registering knowledge source '{n['ks']}'…", kind="step")
    try:
        from azure.search.documents.indexes.models import (
            SearchIndexKnowledgeSource, SearchIndexKnowledgeSourceParameters,
            SearchIndexFieldReference,
        )
    except ImportError:
        stream.error("This azure-search-documents build lacks KnowledgeSource models.",
                     hint="Install the preview pinned in requirements.txt.")
        return
    ks = SearchIndexKnowledgeSource(
        name=n["ks"],
        search_index_parameters=SearchIndexKnowledgeSourceParameters(
            search_index_name=n["index"],
            source_data_fields=[SearchIndexFieldReference(name="id"),
                                SearchIndexFieldReference(name="page_chunk"),
                                SearchIndexFieldReference(name="page_number")]),
    )
    index_client.create_or_update_knowledge_source(knowledge_source=ks)
    stream.foundry("Knowledge source", n["ks"], kind="knowledge")

    # 4) knowledge base
    stream.status(f"Creating knowledge base '{n['kb']}' (answer synthesis)…", kind="step")
    try:
        from azure.search.documents.indexes.models import (
            KnowledgeBase, KnowledgeSourceReference,
            KnowledgeRetrievalLowReasoningEffort, KnowledgeRetrievalOutputMode,
            KnowledgeBaseAzureOpenAIModel, AzureOpenAIVectorizerParameters as KBParams,
        )
    except ImportError:
        stream.error("This azure-search-documents build lacks KnowledgeBase models.",
                     hint="Install the preview pinned in requirements.txt.")
        return
    model = KnowledgeBaseAzureOpenAIModel(azure_open_ai_parameters=KBParams(
        resource_url=n["foundry_endpoint"], deployment_name=n["chat"], model_name=n["chat"]))
    index_client.create_or_update_knowledge_base(KnowledgeBase(
        name=n["kb"], knowledge_sources=[KnowledgeSourceReference(name=n["ks"])],
        retrieval_reasoning_effort=KnowledgeRetrievalLowReasoningEffort(),
        output_mode=KnowledgeRetrievalOutputMode.ANSWER_SYNTHESIS, models=[model]))
    stream.foundry("Knowledge base", n["kb"], kind="knowledge")
    stream.status("Setup complete — you can run a query now.", kind="ok")
    stream.emit("setup_done", {"ready": True})


def run(stream: EventStream, payload: dict) -> None:
    n = _names()
    if not n["search_endpoint"]:
        stream.error("SEARCH_ENDPOINT is not set — run infra/provision first.")
        return
    query = (payload or {}).get("query") or DEFAULT_QUERY
    cred = get_credential()
    try:
        from azure.search.documents.knowledgebases import KnowledgeBaseRetrievalClient
        from azure.search.documents.knowledgebases.models import (
            KnowledgeBaseRetrievalRequest, KnowledgeBaseMessage, KnowledgeBaseMessageTextContent,
        )
    except ImportError:
        stream.error("KnowledgeBaseRetrievalClient not in this azure-search-documents build.",
                     hint="Install the preview pinned in requirements.txt, or run setup first.")
        return

    kb_client = KnowledgeBaseRetrievalClient(
        endpoint=n["search_endpoint"], knowledge_base_name=n["kb"], credential=cred)
    request = KnowledgeBaseRetrievalRequest(messages=[
        KnowledgeBaseMessage(role="assistant", content=[KnowledgeBaseMessageTextContent(text=SYSTEM)]),
        KnowledgeBaseMessage(role="user", content=[KnowledgeBaseMessageTextContent(text=query)]),
    ])

    stream.user(query)
    stream.status("Planning → parallel subqueries → semantic rank → synthesis…", kind="step")
    result = kb_client.retrieve(request)

    answer = result.response[0].content[0].text
    stream.answer(answer)

    activity = getattr(result, "activity", None) or []
    subquery_count = 0
    for step in activity:
        label = getattr(step, "type", None) or step.__class__.__name__
        q = getattr(step, "query", None) or getattr(step, "search", None)
        if q is not None and hasattr(q, "search"):
            q = q.search
        if q:
            stream.subquery(str(q))
            if "query" in str(label).lower() or "search" in str(label).lower():
                subquery_count += 1
        stream.foundry("Activity", label, kind="run")

    references = getattr(result, "references", None) or []
    for ref in references:
        # Extract full source data and metadata for interactive reference display
        source_data = str(getattr(ref, "source_data", "") or "")
        ref_id = str(getattr(ref, "ref_id", getattr(ref, "id", "?")))
        doc_key = getattr(ref, "doc_key", None)
        score = getattr(ref, "score", None)
        
        stream.citation(
            ref_id=ref_id,
            text=source_data,  # Send full text, not truncated
            page=doc_key,
            score=score,
        )
    
    stream.metric("Subqueries", subquery_count if subquery_count > 0 else len(activity))
