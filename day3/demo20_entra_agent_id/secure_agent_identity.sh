#!/usr/bin/env bash
# Day 3 · Demo 20 — Give an agent its own Entra identity + least-privilege RBAC
# =============================================================================
# The keyless pattern for "Secure AI agents with Microsoft Entra ID": create a
# user-assigned MANAGED IDENTITY for the agent, then grant it ONLY the role it
# needs on the Foundry account (Cognitive Services User). The agent authenticates
# with this identity via DefaultAzureCredential — no secrets, fully auditable.
#
# Prereqs: az login  ·  jq optional. Reads .env (FOUNDRY_ACCOUNT_ENDPOINT etc).
set -euo pipefail

# Load repo .env if present
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
[ -f "$ROOT/.env" ] && set -a && . "$ROOT/.env" && set +a

RG="${ENV_RESOURCE_GROUP:-rg-agentic-ai-demos}"
LOCATION="${ENV_REGION:-australiaeast}"
IDENTITY_NAME="${AGENT_IDENTITY_NAME:-id-agent-demo20}"
# Derive the Foundry account name from its endpoint (foundry-xxx.services.ai...)
ACCOUNT_NAME="${FOUNDRY_ACCOUNT_NAME:-$(echo "${FOUNDRY_ACCOUNT_ENDPOINT:-}" | sed -E 's#https?://([^.]+).*#\1#')}"

echo "==> Signed-in identity (the human deploying the agent):"
az ad signed-in-user show --query "{name:userPrincipalName, oid:id}" -o table 2>/dev/null \
  || az account show --query "{user:user.name, tenant:tenantId}" -o table

echo "==> 1) Create a user-assigned managed identity for the agent: $IDENTITY_NAME"
az identity create -g "$RG" -n "$IDENTITY_NAME" -l "$LOCATION" -o table
PRINCIPAL_ID=$(az identity show -g "$RG" -n "$IDENTITY_NAME" --query principalId -o tsv)
CLIENT_ID=$(az identity show -g "$RG" -n "$IDENTITY_NAME" --query clientId -o tsv)
echo "    principalId=$PRINCIPAL_ID  clientId=$CLIENT_ID"

echo "==> 2) Resolve the Foundry account scope: $ACCOUNT_NAME"
SCOPE=$(az cognitiveservices account show -n "$ACCOUNT_NAME" -g "$RG" --query id -o tsv)
echo "    scope=$SCOPE"

echo "==> 3) Grant LEAST PRIVILEGE — 'Cognitive Services User' (call models, no admin):"
az role assignment create \
  --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --role "Cognitive Services User" \
  --scope "$SCOPE" -o table

echo "==> 4) Verify the assignment:"
az role assignment list --assignee "$PRINCIPAL_ID" --all \
  --query "[].{role:roleDefinitionName, scope:scope}" -o table

cat <<EOF

Done. The agent now has its own Entra identity with exactly one role.
Use it from code keylessly:

  from azure.identity import ManagedIdentityCredential
  cred = ManagedIdentityCredential(client_id="$CLIENT_ID")

Next: register this as a first-class Entra Agent ID (portal_runbook.md) and
govern the whole fleet from the M365 admin center (agent365_runbook.md).
EOF
