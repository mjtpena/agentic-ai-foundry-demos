# Day 3 · Demo 14 — Create a Guardrail policy (slide 23)

Foundry guardrail policies are enforced by **Azure Policy**. This demo creates a
custom policy that restricts which models may be deployed (the slide-21 "allowed
list of models" idea) and assigns it to your resource group.

```bash
./create_guardrail_policy.sh                  # Audit effect, scope = resource group
EFFECT=Deny ./create_guardrail_policy.sh       # block non-approved model deploys
SCOPE=subscription ./create_guardrail_policy.sh
```

| File | Role |
|---|---|
| `guardrail_policy.json` | The policy definition (allowed-models rule + Audit/Deny effect). |
| `create_guardrail_policy.sh` | Creates the definition and assigns it via `az policy`. |
| `portal_runbook.md` | The Foundry portal wizard equivalent (Operate › Compliance). |

Verify / observe violations (feeds demo 15):
```bash
az policy state summarize --resource-group rg-agentic-ai-demos -o table
```
Reference: https://learn.microsoft.com/en-us/azure/foundry/control-plane/quickstart-create-guardrail-policy
