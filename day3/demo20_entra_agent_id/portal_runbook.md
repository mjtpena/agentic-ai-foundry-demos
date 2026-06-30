# Day 3 · Demo 20 — Secure AI agents with Microsoft Entra ID (portal runbook)

> Module 7 · "Secure AI agents with Microsoft Entra ID"

Goal: give an agent a **first-class Entra identity** and govern its access with
RBAC — least privilege, keyless, fully auditable. Pair this runbook with the
runnable [`inspect_identity.py`](inspect_identity.py) (shows the live token
claims + role assignments) and [`secure_agent_identity.sh`](secure_agent_identity.sh)
(creates the identity + role from the CLI).

## A · Why Entra for agents
- Agents are non-human identities. Treating them as first-class Entra principals
  means the **same** controls you use for users apply: Conditional Access, RBAC,
  audit logs, lifecycle.
- **Entra Agent ID** gives each agent its own directory object, so you can see
  every agent in the tenant, who owns it, and what it can reach.

## B · Register / view the agent's identity (Entra admin center)
1. `https://entra.microsoft.com` → **Identity** → **Applications** →
   **Enterprise applications** (agents created in Foundry surface here, and the
   newer **Agent ID** view lists agent identities directly).
2. Open your agent's identity. Note its **Object ID** and **Application ID** —
   these match the `oid` / `appid` claims `inspect_identity.py` prints.
3. **Owners** — assign a human owner (accountability).
4. **Conditional Access** — optionally scope the agent (e.g. only from trusted
   networks).

## C · Grant least-privilege RBAC (Azure portal)
1. Foundry account → **Access control (IAM)** → **Add role assignment**.
2. Role: **Cognitive Services User** (call models) — *not* Owner/Contributor.
3. Assign to the agent's **managed identity / Agent ID**.
4. **Review + assign**. Confirm under **Role assignments**.

> CLI equivalent: `secure_agent_identity.sh` creates a user-assigned managed
> identity and grants exactly this role on the account scope.

## D · Prove it's keyless
- Run `python day3/demo20_entra_agent_id/inspect_identity.py`.
- It acquires a token with **DefaultAzureCredential** (no keys), decodes the
  claims (`oid`, `appid`, `tid`, `aud`, `scp`), and lists the RBAC roles the
  identity holds. That's the whole trust chain, visible end to end.

## Talking points
- No secrets in code or config — credentials are never the leak vector.
- Remove access by removing a role assignment; disable the agent by disabling
  its identity. Same muscle memory as managing a user.
- This is the per-agent control. **Agent 365** (Module 8,
  [`agent365_runbook.md`](agent365_runbook.md)) takes it fleet-wide.

Reference:
https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/rbac-azure-ai-foundry
