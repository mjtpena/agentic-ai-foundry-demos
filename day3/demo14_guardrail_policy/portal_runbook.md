# Day 3 · Demo 14 — Create a Guardrail policy (portal version, slide 23)

The no-code path. The CLI version (`create_guardrail_policy.sh`) does the
equivalent via Azure Policy.

## Steps
1. Sign in to Foundry; ensure **New Foundry** toggle is **on**.
2. Toolbar → **Operate** → left pane **Compliance** → **Create policy**.
3. **Add controls** — choose guardrail controls (content-safety filters, prompt
   shields, groundedness checks). These are the minimum settings a deployment
   needs to be compliant. Select **Add control** for each.
4. **Next → scope** — choose a **subscription** or **resource group**
   (`rg-agentic-ai-demos`), then **Select**.
5. **Next → exceptions** — optionally exempt resource groups or individual model
   deployments.
6. **Next → review** — name the policy, review scope/exceptions/controls, **Submit**.
7. **Verify** — Compliance → **Policies** tab → confirm name, scope, and status.

Reference: https://learn.microsoft.com/en-us/azure/foundry/control-plane/quickstart-create-guardrail-policy
