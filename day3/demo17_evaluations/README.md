# Day 3 · Demo 17 — Evaluate, monitor and optimize AI apps and agents

> Module 7 · "Evaluate, monitor and optimize AI apps and agents"

You can't govern what you can't measure. This demo runs Foundry's two evaluator
families over a small dataset of agent answers and produces a scorecard:

| Family | Evaluators | Scale | Graded by |
|---|---|---|---|
| **Quality** (AI-assisted) | Groundedness · Relevance · Coherence · Fluency | 1–5 | a judge model |
| **Risk & safety** | Violence · Hate/Unfairness · Sexual · Self-harm | 0–7 severity | Foundry safety service |

The dataset ([`eval_dataset.jsonl`](eval_dataset.jsonl)) is `{query, context,
response}` rows. **Row 2** hallucinates a CEO and **row 4** gives unsafe advice —
so groundedness drops and the safety evaluators light up. That's the teaching
moment: evaluation is how you catch regressions *before and after* deployment,
and the scores flow into the Control Plane's Observability + Compliance panes.

## Run it
```bash
pip install azure-ai-evaluation azure-identity python-dotenv
az login
python day3/demo17_evaluations/evaluate_agent.py
```

Env:
- `FOUNDRY_ACCOUNT_ENDPOINT` — Azure OpenAI endpoint of the judge model
- `MODEL_DEPLOYMENT_NAME` — judge deployment (default `gpt-4o`)
- `AZURE_AI_PROJECT_ENDPOINT` *(optional)* — enables the risk & safety evaluators

If `azure-ai-evaluation` or the project endpoint is missing, the script degrades
clearly (quality-only, or a one-line install hint) rather than crashing.

## In the live console
The UI demo (**Day 3 · Evaluations**) runs the same two families with
always-installed dependencies — model-as-judge for quality, Azure AI Content
Safety for the 0–7 safety severities — so it's click-to-run even without the
preview SDK. **View Source** there shows this real `azure-ai-evaluation` script.

Reference:
https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/evaluate-sdk
