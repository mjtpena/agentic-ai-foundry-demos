# Day 3 · Demo 13 — Foundry Control Plane capabilities (slide 16)

Portal tour of the **Foundry Control Plane** — the fleet-wide command center for
governing AI agents, models, and tools across projects in a subscription.

## Open it
1. Foundry portal (`https://ai.azure.com`) — ensure the **New Foundry** toggle is **on**.
2. Top-right toolbar → **Operate**. Everything below lives under panes here.

## Panes to walk
| Pane | What to show |
|---|---|
| **Assets** | Unified, searchable inventory of every agent / model / tool across projects. Auto-discovered. (`Operate › Assets › Agents`) |
| **Observability** | Health, cost, token usage, and behavior per agent — before and after deployment. |
| **Compliance** | Guardrail **Policies**, per-asset violations, **Guardrails** coverage, and **Security posture** (Defender for Cloud + Purview). |
| **Security** | Entra Agent ID, runtime defense, sensitive-data protection. |

## Why it matters (talking points)
- Enterprises are scaling from tens to **thousands** of agents — ungoverned, that doesn't scale.
- As an agent crosses internal⇄external boundaries you must: allow only trusted
  tools/content in, protect sensitive data from leaking out, and keep agents on task.
- Integrates **Microsoft Defender, Purview, and Entra** for governance at scale.

This sets up the next three demos: **#14** create a guardrail policy, **#15** fix
violations, **#16** configure guardrails/content safety.

Reference: https://learn.microsoft.com/en-us/azure/foundry/control-plane/overview
