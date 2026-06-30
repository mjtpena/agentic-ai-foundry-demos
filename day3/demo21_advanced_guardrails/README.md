# Day 3 · Demo 21 — Advanced Guardrails for enterprise agents

> Module 7 · "Implement Azure AI Content Safety" / "Manage compliance and security"

Demo 16 covers **input moderation** (harm categories, blocklist, jailbreak).
This demo is the rest of the Foundry guardrail suite — the **output-side and
boundary** controls that matter once an agent reaches across the
internal⇄external boundary:

| # | Guardrail | Threat it stops | On this resource |
|---|---|---|---|
| 1 | **Indirect prompt injection (XPIA)** | attack hidden in a *retrieved document* / tool output (the #1 RAG/agent threat) | ✅ live |
| 2 | **Protected material — text** | copyrighted text leaking out of the model | ✅ live |
| 3 | **Protected material — code** | code lifted from public repositories | ✅ live |
| 4 | **Groundedness** | hallucination — answer drifts off its sources | ⚠️ preview, region-gated (degrades gracefully) |
| 5 | **PII detection & redaction** | personal data leaking (Azure AI Language) | ✅ live |

All calls hit real Foundry / Cognitive Services / Language REST endpoints,
keyless via Entra — no mocks. Verified live: XPIA flags the poisoned document
(not the clean user prompt), protected text + code both detected, PII redacted to
`Call me at ************ … SSN ***********`.

## Run it
```bash
pip install azure-identity python-dotenv
az login
python day3/demo21_advanced_guardrails/advanced_guardrails.py
```
Env: `FOUNDRY_ACCOUNT_ENDPOINT` (the Foundry multi-service account — it also
fronts the Language PII endpoint).

## In the live console
The UI demo (**Day 3 · Advanced Guardrails**) runs the full suite on curated
scenarios, or screens custom text (harm + PII + protected material). **View
Source** shows this script.

> Groundedness returns *"not yet available in this region"* on `australiaeast`.
> The demo shows the real request and the graceful fallback — enable it in a
> [supported region](https://learn.microsoft.com/en-us/azure/ai-services/content-safety/concepts/groundedness)
> and it lights up unchanged. See [`portal_runbook.md`](portal_runbook.md) to
> wire these into a Foundry Guardrail policy.
