# Day 3 · Demo 15 — View and fix compliance violations (slide 26)

Portal demo: find model deployments that violate a guardrail policy and remediate
them. Pairs with **#14** (which creates the policy) — run that first, ideally
with `EFFECT=Audit` so violations show up to fix.

## By policy
1. **Operate › Compliance › Policies**.
2. Set the project filter to **All projects** to see the whole subscription.
3. Find any policy with **Violations detected** in the *Policy Compliance* column.
4. Select the policy → in the pane, pick an **asset** to compare its guardrail
   settings against the policy's requirements.
5. Select **Fix now** → adjust the deployment's guardrail configuration to meet
   the policy → **Save**. Status updates within a few minutes.

## By asset
1. **Operate › Compliance › Assets** (toggle Policy/Assets).
2. Review deployments; inspect any marked **Violations detected**.
3. Select the row → review the governing policies and the noncompliant specifics.
4. **View in Build** → modify the guardrail configuration → save. Re-check all
   policies that touch the asset to reach full compliance.

> Tie-in to code: the Azure-Policy version of "violation" is visible from the CLI
> too — after running demo 14 in Audit mode:
> `az policy state summarize --resource-group rg-agentic-ai-demos -o table`

Reference: https://learn.microsoft.com/en-us/azure/foundry/control-plane/how-to-manage-compliance-security#view-and-fix-compliance-violations
