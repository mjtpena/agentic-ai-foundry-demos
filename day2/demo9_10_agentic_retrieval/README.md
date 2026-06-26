# Day 2 · Demos 9 & 10 — Agentic retrieval with Azure AI Search (slides 51-61)

Builds the full agentic-retrieval pipeline, then queries it. Demo 9 = create the
knowledge source (slide 51); Demo 10 = the portal version (slide 61,
`portal_runbook.md`). The Python here covers the whole flow end to end.

```bash
# one-time: load the Earth-at-Night sample docs into blob storage
../../infra/upload_sample_data.sh

pip install "azure-search-documents>=11.7.0b1" azure-identity python-dotenv
az login
python 01_create_knowledge_source.py   # earth-at-night index + earth-at-night-ks
python 02_create_knowledge_base.py      # earth-at-night-kb (answer synthesis)
python 03_query_knowledge_base.py       # the Phoenix / December-brightening query
```

| File | Slide | Does |
|---|---|---|
| `01_create_knowledge_source.py` | 51, 60 | hybrid index + upload docs + `SearchIndexKnowledgeSource` |
| `02_create_knowledge_base.py` | 54-55 | `KnowledgeBase` w/ low reasoning + answer synthesis |
| `03_query_knowledge_base.py` | 56, 61 | `retrieve` with the exact multi-part slide query |
| `portal_runbook.md` | 61 | the no-code Azure-portal path |

> **Preview SDK:** the `KnowledgeSource` / `KnowledgeBase` objects are in the
> `azure-search-documents` preview. If your installed build uses different class
> names, the scripts print a clear message and point you to the portal runbook —
> the concepts and steps are identical.

If you didn't load blob data, `01` falls back to a small built-in Earth-at-Night
sample so the pipeline still runs.

Env: `SEARCH_ENDPOINT`, `FOUNDRY_ACCOUNT_ENDPOINT`, `EMBEDDING_DEPLOYMENT`, `MODEL_DEPLOYMENT_NAME`.
