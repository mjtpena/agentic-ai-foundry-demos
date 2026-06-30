# Day 3 · Demo 18 — AI Red Teaming Agent

> Module 7 · "Manage compliance and security in Microsoft Foundry"

Foundry's **AI Red Teaming Agent** automates adversarial testing. It takes seed
attack **objectives** across risk categories, mutates them with PyRIT **attack
strategies** (Base64, Flip, Morse, ROT13, composed…), fires them at your target
model or agent, and grades every response — producing an **Attack Success Rate
(ASR) scorecard** you can track release over release.

A **low ASR is the goal**: it's hard evidence that your guardrails (demos 14 &
16) actually hold up under attack, not just on paper.

## Run it (real RedTeam SDK)
```bash
pip install "azure-ai-evaluation[redteam]" azure-identity openai python-dotenv
az login
python day3/demo18_red_team/run_red_team.py
```

Env:
- `AZURE_AI_PROJECT_ENDPOINT` — the Foundry project (required by `RedTeam`)
- `FOUNDRY_ACCOUNT_ENDPOINT` — Azure OpenAI endpoint of the target model
- `MODEL_DEPLOYMENT_NAME` — target deployment (default `gpt-4o`)

> The real scan is PyRIT-backed and runs for several minutes. The script keeps
> the objective/category count small so a live run stays manageable; raise
> `NUM_OBJECTIVES` and add strategies for a fuller sweep.

## In the live console
The UI demo (**Day 3 · AI Red Teaming**) runs the same harness — objectives ×
attack strategies against the selected live model, graded with a refusal
heuristic + Azure AI Content Safety — but finishes in seconds, so it's
click-to-run. **View Source** there shows this real `RedTeam` script.

The objectives are phrased abstractly on purpose: the point is to exercise the
attack harness and watch a well-aligned model **refuse**, not to elicit harmful
content.

Reference:
https://learn.microsoft.com/en-us/azure/ai-foundry/how-to/develop/run-scans-ai-red-teaming-agent
