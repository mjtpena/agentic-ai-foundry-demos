#!/usr/bin/env bash
# Day 3 · Demo 14 — Create a Guardrail policy via Azure CLI (slide 23)
#
# The Foundry "Guardrail policy" (Operate > Compliance) is enforced underneath by
# Azure Policy. This script creates a custom policy DEFINITION that restricts
# which models can be deployed, then ASSIGNS it to your resource group — the
# az-scriptable equivalent of the slide-23 wizard and the slide-21 "allowed list
# of models" built-in policy.
#
# Default effect is 'Audit' (safe: flags violations). Pass EFFECT=Deny to block.
#
# Usage:
#   ./create_guardrail_policy.sh                 # audit, scope = resource group
#   EFFECT=Deny SCOPE=subscription ./create_guardrail_policy.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../../infra/00-variables.sh"

POLICY_NAME="${POLICY_NAME:-aa-allowed-foundry-models}"
EFFECT="${EFFECT:-Audit}"
SCOPE="${SCOPE:-resourcegroup}"   # 'resourcegroup' or 'subscription'

[ -n "${SUBSCRIPTION_ID}" ] || die "Run 'az login' first."

say "Creating policy definition '${POLICY_NAME}' (effect default: Audit)"
az policy definition create \
  --name "${POLICY_NAME}" \
  --display-name "Accelerate Agentic AI - Allowed Foundry models only" \
  --description "Restrict model deployments to an approved list (slide 21/23)." \
  --rules   "@${SCRIPT_DIR}/guardrail_policy.json#properties.policyRule" \
  --params  "@${SCRIPT_DIR}/guardrail_policy.json#properties.parameters" \
  --mode All -o none 2>/dev/null || \
  az policy definition create --name "${POLICY_NAME}" \
    --display-name "Accelerate Agentic AI - Allowed Foundry models only" \
    --rules "$(python3 -c "import json;print(json.dumps(json.load(open('${SCRIPT_DIR}/guardrail_policy.json'))['properties']['policyRule']))")" \
    --params "$(python3 -c "import json;print(json.dumps(json.load(open('${SCRIPT_DIR}/guardrail_policy.json'))['properties']['parameters']))")" \
    --mode All -o none
ok "Policy definition created"

if [ "${SCOPE}" = "subscription" ]; then
  ASSIGN_SCOPE="/subscriptions/${SUBSCRIPTION_ID}"
else
  ASSIGN_SCOPE="/subscriptions/${SUBSCRIPTION_ID}/resourceGroups/${RESOURCE_GROUP}"
fi

say "Assigning policy at scope: ${ASSIGN_SCOPE}  (effect=${EFFECT})"
az policy assignment create \
  --name "${POLICY_NAME}-assign" \
  --display-name "Allowed Foundry models (${EFFECT})" \
  --policy "${POLICY_NAME}" \
  --scope "${ASSIGN_SCOPE}" \
  --params "{\"effect\":{\"value\":\"${EFFECT}\"}}" -o none
ok "Policy assigned."

echo
say "Verify:  az policy assignment list --scope ${ASSIGN_SCOPE} -o table"
say "Compliance state appears within a few minutes:"
say "  az policy state summarize --resource-group ${RESOURCE_GROUP} -o table"
say "To remove: az policy assignment delete -n ${POLICY_NAME}-assign --scope ${ASSIGN_SCOPE}"
