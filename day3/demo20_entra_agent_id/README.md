# Day 3 · Demo 20 — Secure AI agents with Microsoft Entra ID (+ Agent 365)

> Module 7 · "Secure AI agents with Microsoft Entra ID"
> Module 8 · "Bring agent observability, security and governance with Agent 365"

Agents are non-human identities. Securing them with **Entra** means the same
controls you use for users — keyless auth, RBAC, Conditional Access, audit,
lifecycle — apply to agents too. **Entra Agent ID** gives each agent its own
directory object; **Agent 365** governs the whole fleet from the M365 admin
center.

## Files
| File | What it does |
|---|---|
| [`inspect_identity.py`](inspect_identity.py) | Acquires an Entra token (keyless), decodes the claims (oid/appid/tid/aud/scp), lists the RBAC roles the identity holds. |
| [`secure_agent_identity.sh`](secure_agent_identity.sh) | CLI: create a user-assigned managed identity for an agent and grant it least-privilege `Cognitive Services User` on the Foundry account. |
| [`portal_runbook.md`](portal_runbook.md) | Register / view an Entra Agent ID and assign RBAC in the portal. |
| [`agent365_runbook.md`](agent365_runbook.md) | **Module 8** — Agent 365 IT admin control plane in the M365 admin center. |

## Run it
```bash
pip install azure-identity python-dotenv
az login
python day3/demo20_entra_agent_id/inspect_identity.py     # show the live identity + roles
bash  day3/demo20_entra_agent_id/secure_agent_identity.sh  # create identity + least-privilege role
```

## In the live console
The UI demo (**Day 3 · Entra Agent ID**) acquires a token, decodes the claims,
and lists the identity's RBAC role assignments live — read-only and keyless.
**View Source** shows `inspect_identity.py`.

Reference:
https://learn.microsoft.com/en-us/azure/ai-foundry/concepts/rbac-azure-ai-foundry
