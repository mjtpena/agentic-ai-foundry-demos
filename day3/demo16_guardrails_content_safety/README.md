# Day 3 · Demo 16 — Configure guardrails & content safety (slides 48-49)

Foundry guardrails run on **Azure AI Content Safety**. These scripts drive that
engine directly so you can show the controls working in code, then mirror them in
the portal wizard (`portal_runbook.md`).

```bash
pip install azure-ai-contentsafety azure-identity python-dotenv
az login
python configure_content_safety.py     # harm categories + blocklist + prompt shield
python test_guardrails.py               # ALLOW/BLOCK table at a severity threshold
python test_guardrails.py --threshold 2 # stricter
```

| File | Shows |
|---|---|
| `configure_content_safety.py` | `analyze_text` across Hate/Self-harm/Sexual/Violence, a custom **blocklist**, and a **prompt shield** (jailbreak) check. |
| `test_guardrails.py` | Playground-style "annotate & block" verdicts with a tunable severity threshold. |
| `portal_runbook.md` | The Build › Guardrails wizard (create, assign, test). |

All test prompts are safe to run — the "unsafe" examples are abusive/threatening
*phrasings* used only to trip the classifier; none contain harmful instructions.

Env: `FOUNDRY_ACCOUNT_ENDPOINT`. Role: `Cognitive Services User`.
Reference: https://learn.microsoft.com/en-us/azure/foundry/guardrails/how-to-create-guardrails
