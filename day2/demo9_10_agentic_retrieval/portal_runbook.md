# Day 2 · Demo 10 — Agentic retrieval in the Azure portal (slide 61)

The no-code path to the same result as the Python scripts in this folder. Uses a
**blob** knowledge source (auto-generates the index) over the Earth-at-Night
sample data that `infra/upload_sample_data.sh` loaded.

## 1. Configure access (RBAC)
`infra/provision.sh` already did most of this. Confirm on the **search service**:
- Role-based access enabled; system-assigned managed identity on.
- Your account has **Search Service Contributor**, **Search Index Data
  Contributor**, **Search Index Data Reader**.
- On **storage**, the search identity has **Storage Blob Data Reader**.
- On the **Foundry resource**, the search identity has **Cognitive Services User**.

## 2. Create a knowledge source
1. Search service › **Agentic retrieval › Knowledge sources › Add › Azure blob (Indexed)**.
2. Name `earth-at-night-ks`; pick the subscription, storage account, and the
   `earth-at-night-data` container.
3. Check **Authenticate using managed identity** (System-assigned).
4. **Enable text vectorization › Add vectorizer**: kind **Microsoft Foundry**,
   pick your subscription/project and the `text-embedding-3-large` deployment,
   auth **System assigned identity**. Save.
5. Create the knowledge source.

## 3. Create a knowledge base
1. **Agentic retrieval › Knowledge bases › Add**.
2. Name `earth-at-night-kb`.
3. **Chat completion model › Add model deployment**: Microsoft Foundry, pick your
   LLM deployment (`gpt-4o`), auth System assigned identity. Save.
4. Knowledge sources → select `earth-at-night-ks`. Create. (Answer synthesis is on by default.)

## 4. Test
Send this in the chat playground:

> Why do suburban belts display larger December brightening than urban cores even
> though absolute light levels are higher downtown? Why is the Phoenix nighttime
> street grid so sharply visible from space, whereas large stretches of the
> interstate between midwestern cities remain comparatively dim?

Review the synthesized, citation-backed answer, then open the **debug** icon to
see the activity log (query plan + subqueries).

Reference: https://learn.microsoft.com/en-us/azure/search/search-get-started-agentic-retrieval
