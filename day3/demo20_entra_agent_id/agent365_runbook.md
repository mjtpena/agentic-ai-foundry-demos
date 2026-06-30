# Day 3 · Demo 20b — Agent 365: IT admin control plane for AI agents (portal runbook)

> Module 8 · "Bring agent observability, security and governance with Agent 365"

Where the Foundry Control Plane governs agents **per project / per developer**,
**Agent 365** is the **IT admin** control plane — it manages every agent across
the tenant from the **Microsoft 365 admin center**, with the same registry,
identity, security and lifecycle tooling IT already uses for users and apps.

This is a portal tour (no SDK) — Agent 365 + the M365 admin center are
admin-surface features.

## A · Open the Agents area
1. `https://admin.microsoft.com` (M365 admin center) → **Copilot** / **Agents**
   (the **Agent 365** admin experience).
2. The **registry** lists every agent across the org — built in Copilot Studio,
   Foundry, or partner tools — auto-discovered, with owner, source and status.

## B · The four things to show
| Pane | What to demonstrate |
|---|---|
| **Registry** | One inventory of all agents tenant-wide. Filter by owner, source, status. The "who has deployed what" answer IT couldn't get before. |
| **Identity** | Each agent has an **Entra Agent ID** (ties back to demo 20a). Conditional Access, lifecycle, ownership — managed like a user. |
| **Security** | Defender + Purview signals per agent: risky behavior, sensitive-data access, DLP. Quarantine / disable an agent. |
| **Governance** | Policies and access reviews applied across the fleet; usage + cost reporting for chargeback. |

## C · Foundry Control Plane + Agent 365 together
- **Foundry Control Plane** = builder/operator plane (observability, evaluations,
  guardrails, content safety — demos 13–19).
- **Agent 365** = IT admin plane (tenant-wide registry, identity, security,
  lifecycle).
- Same agent, two governance lenses. Show an agent in the Foundry Control Plane
  Observability pane, then the *same* agent in the Agent 365 registry — one is
  how you build/measure it, the other is how IT governs it at scale.

## D · Frontier Firm / Microsoft 365 E7
- Agent 365 capabilities land with **Microsoft 365 E7** — the "Frontier Firm"
  SKU that bundles agent governance for organizations scaling from tens to
  **thousands** of agents.
- Talking point: at that scale, ungoverned agents are an audit and security
  liability; E7 makes the agent fleet a managed, first-class part of the tenant.

## Talking points
- IT gets one place to answer: *Which agents exist? Who owns them? What can they
  touch? Are any behaving badly?*
- Lifecycle parity with users: provision, review, disable, offboard.
- Builders keep velocity in Foundry; IT keeps control in Agent 365.

References:
- Agent 365 — https://www.microsoft.com/en-us/microsoft-365/agents
- Manage agents in the M365 admin center —
  https://learn.microsoft.com/en-us/microsoft-365/admin/
