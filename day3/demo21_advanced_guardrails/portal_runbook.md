# Day 3 · Demo 21 — Wire advanced guardrails into a Foundry policy (portal runbook)

> Module 7 · "Implement Azure AI Content Safety"

The code demo calls each detection directly. In production you attach them to an
agent as a **Guardrail** in the Foundry Control Plane, so they run automatically
on every turn with an **Annotate / Block** action.

## A · Open Guardrails
1. Foundry portal (`https://ai.azure.com`, New Foundry on) → **Operate** →
   **Compliance** → **Guardrails** (or **Protect & govern → Guardrails**).
2. **+ Create** → select the controls to combine into one policy.

## B · Add the advanced controls
| Control | Wizard toggle | Action |
|---|---|---|
| Indirect prompt injection | **Prompt Shields** → enable *document/indirect* scanning | Block |
| Protected material (text) | **Protected material for text** | Annotate (or Block) |
| Protected material (code) | **Protected material for code** | Annotate |
| Groundedness | **Groundedness detection** (region-dependent) | Annotate |
| PII | **Sensitive information** (via Azure AI Language / Purview) | Redact / Block |

Set a **severity threshold** per harm category (the dial demo 16's
`test_guardrails.py` exercises).

## C · Attach + test
1. Attach the policy to your agent / deployment.
2. **Try in Playground** — paste a prompt with a poisoned document or a PII
   string and watch the **annotate-and-block** verdict.
3. Violations surface in **Compliance → Violations** (demo 15) and roll up to the
   Control Plane Compliance pane.

## Talking points
- Input moderation (demo 16) stops bad input; these stop **bad output and
  boundary attacks** — together they're defense in depth.
- XPIA is the guardrail most teams miss: the user prompt is clean, the *retrieved
  content* carries the attack. Essential for any RAG or tool-using agent.
- Everything is keyless (Entra) and auditable — pairs with demo 20.

References:
- Prompt Shields — https://learn.microsoft.com/en-us/azure/ai-services/content-safety/concepts/jailbreak-detection
- Protected material — https://learn.microsoft.com/en-us/azure/ai-services/content-safety/concepts/protected-material
- Groundedness — https://learn.microsoft.com/en-us/azure/ai-services/content-safety/concepts/groundedness
- PII — https://learn.microsoft.com/en-us/azure/ai-services/language-service/personally-identifiable-information/overview
