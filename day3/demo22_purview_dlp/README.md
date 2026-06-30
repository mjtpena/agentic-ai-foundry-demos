# Day 3 · Demo 22 — Purview & DLP for AI agents (portal runbook)

> Module 7 · "Manage compliance and security in Microsoft Foundry"

Guardrails (demos 16/21) stop unsafe *content*. **Microsoft Purview** governs
the *data* — it answers the compliance/security questions an enterprise data
office asks about agents: *What sensitive data are agents touching? Is it leaking?
Can we prove it for an audit?* Foundry integrates Purview signals into the
Control Plane Compliance + Security posture panes.

This is a portal tour (no SDK) — Purview is an admin/compliance surface.

## A · DSPM for AI (the starting point)
1. Purview portal (`https://purview.microsoft.com`) → **Data Security Posture
   Management (DSPM) for AI**.
2. Show the **overview**: prompts/responses volume across Copilot + custom AI
   apps (incl. Foundry agents), sensitive-data interactions, and risky activity.
3. **Recommendations** — one-click policies (e.g. "Detect risky interactions in
   AI apps", "Protect sensitive data referenced in AI").

## B · The four controls to demonstrate
| Control | What it does for agents |
|---|---|
| **Sensitivity labels + auto-labeling** | Classify data (Confidential, Highly Confidential). Agents inherit and respect labels on the content they retrieve. |
| **Data Loss Prevention (DLP)** | Policy: block/alert when an agent's grounding or output includes sensitive info types (credit cards, health, secrets). DLP for Copilot/AI extends to agent interactions. |
| **Communication Compliance** | Detects risky/abusive prompts & responses in agent conversations. |
| **Insider Risk + Audit** | Every agent prompt/response is auditable; risky-user signals feed Insider Risk Management. |

## C · Wire DLP to AI (the core demo)
1. Purview → **Data Loss Prevention** → **+ Create policy** → location
   **Microsoft 365 Copilot / AI apps** (covers agent interactions).
2. Condition: content contains **Sensitive info types** (e.g. *Credit Card
   Number*, *Australia Tax File Number*) or a **sensitivity label**.
3. Action: **Block** the AI from using/processing that content (or **Audit** to
   start). Optionally a policy tip.
4. Save → show a test prompt that references a labeled/sensitive doc being
   blocked or alerted.

## D · Foundry Control Plane ⇄ Purview
- In the **Control Plane → Compliance → Security posture** pane, Purview +
  Defender signals roll up per asset (the "Manage compliance and security" slide).
- DLP/sensitivity protects data **out**; guardrails (16/21) keep bad content
  **in/out**; Entra (20) controls **who/what** the agent is — defense in depth.

## Talking points
- Guardrails ≠ data governance. You need both: content safety *and* data-loss
  controls that understand your sensitivity labels and info types.
- Purview makes agent data flows **auditable and provable** — essential for
  regulated industries.
- It's the same Purview your compliance team already runs for M365 — agents just
  become another governed workload.

References:
- DSPM for AI — https://learn.microsoft.com/en-us/purview/ai-microsoft-purview
- DLP for Copilot / AI — https://learn.microsoft.com/en-us/purview/dlp-microsoft365-copilot-policy
- Purview + AI overview — https://learn.microsoft.com/en-us/purview/ai-microsoft-purview-considerations
