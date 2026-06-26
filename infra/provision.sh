#!/usr/bin/env bash
# =============================================================================
# Accelerate Agentic AI — MASTER provisioning script (Azure CLI)
#
# Creates everything the code demos across Days 1-3 need:
#   • Resource group
#   • Microsoft Foundry account (Azure AI Services, kind=AIServices) + project
#   • Model deployments: gpt-4o, gpt-4.1, gpt-4.1-mini, gpt-5-mini,
#     text-embedding-3-large
#   • Azure AI Search service (Day 2 agentic retrieval)
#   • Storage account + blob container (Earth-at-Night knowledge source)
#   • RBAC role assignments for the signed-in user and Search managed identity
#   • A populated ../.env file consumed by every Python demo
#
# Safe to re-run: every step is idempotent (create-if-absent).
#
# Usage:
#   az login                 # sign in to YOUR subscription first
#   az account set -s "<subscription-id-or-name>"   # optional
#   ./provision.sh
# =============================================================================
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/00-variables.sh"

# --- 0. Pre-flight ----------------------------------------------------------
command -v az >/dev/null 2>&1 || die "Azure CLI ('az') not found. Install: https://aka.ms/azcli"
[ -n "${SUBSCRIPTION_ID}" ] || die "Not logged in. Run 'az login' first."

say "Subscription : ${SUBSCRIPTION_ID}"
say "Location     : ${LOCATION}"
say "Resource grp : ${RESOURCE_GROUP}"
say "Foundry acct : ${FOUNDRY_ACCOUNT}  (project: ${FOUNDRY_PROJECT})"
say "Search       : ${SEARCH_SERVICE} (${SEARCH_SKU})"
say "Storage      : ${STORAGE_ACCOUNT} / ${BLOB_CONTAINER}"
echo
read -r -p "Proceed and create these resources? [y/N] " ans
[[ "${ans:-}" =~ ^[Yy]$ ]] || die "Aborted by user."

# Make sure the providers we touch are registered (no-op if already done).
for ns in Microsoft.CognitiveServices Microsoft.Search Microsoft.Storage; do
  az provider register --namespace "$ns" --wait >/dev/null 2>&1 || true
done

# --- 1. Resource group ------------------------------------------------------
say "Creating resource group"
az group create -n "${RESOURCE_GROUP}" -l "${LOCATION}" -o none
ok "Resource group ${RESOURCE_GROUP}"

# --- 2. Foundry account (Azure AI Services, kind=AIServices) -----------------
say "Creating Microsoft Foundry account (this can take a minute)"
if ! az cognitiveservices account show -n "${FOUNDRY_ACCOUNT}" -g "${RESOURCE_GROUP}" -o none 2>/dev/null; then
  az cognitiveservices account create \
    -n "${FOUNDRY_ACCOUNT}" -g "${RESOURCE_GROUP}" -l "${LOCATION}" \
    --kind AIServices --sku S0 \
    --custom-domain "${FOUNDRY_ACCOUNT}" \
    --assign-identity \
    --yes -o none
fi
ok "Foundry account ${FOUNDRY_ACCOUNT}"
FOUNDRY_ID="$(az cognitiveservices account show -n "${FOUNDRY_ACCOUNT}" -g "${RESOURCE_GROUP}" --query id -o tsv)"

# --- 3. Foundry project (management REST; api-version churns, so fall back) --
say "Creating Foundry project '${FOUNDRY_PROJECT}'"
PROJECT_URL="https://management.azure.com${FOUNDRY_ID}/projects/${FOUNDRY_PROJECT}?api-version=${PROJECTS_API_VERSION}"
if az rest --method put --url "${PROJECT_URL}" \
      --headers "Content-Type=application/json" \
      --body "{\"location\":\"${LOCATION}\",\"identity\":{\"type\":\"SystemAssigned\"},\"properties\":{\"displayName\":\"${FOUNDRY_PROJECT}\",\"description\":\"Accelerate Agentic AI demos\"}}" \
      -o none 2>/dev/null; then
  ok "Project ${FOUNDRY_PROJECT}"
else
  warn "Project creation via REST failed (api-version ${PROJECTS_API_VERSION} may be stale)."
  warn "Open ${FOUNDRY_ACCOUNT_ENDPOINT} in the Foundry portal, create a project named"
  warn "'${FOUNDRY_PROJECT}', copy its endpoint, and paste it into ../.env as PROJECT_ENDPOINT."
fi

# --- 4. Model deployments ---------------------------------------------------
say "Deploying models"
for spec in "${MODEL_DEPLOYMENTS[@]}"; do
  IFS=':' read -r m_name m_format m_version m_sku m_cap <<< "${spec}"
  ver_args=(); [ -n "${m_version}" ] && ver_args=(--model-version "${m_version}")
  if az cognitiveservices account deployment show \
        -n "${FOUNDRY_ACCOUNT}" -g "${RESOURCE_GROUP}" --deployment-name "${m_name}" -o none 2>/dev/null; then
    ok "${m_name} already deployed"; continue
  fi
  if az cognitiveservices account deployment create \
        -n "${FOUNDRY_ACCOUNT}" -g "${RESOURCE_GROUP}" \
        --deployment-name "${m_name}" \
        --model-name "${m_name}" --model-format "${m_format}" "${ver_args[@]}" \
        --sku-name "${m_sku}" --sku-capacity "${m_cap}" -o none 2>/dev/null; then
    ok "Deployed ${m_name} (${m_sku}, ${m_cap}k TPM)"
  else
    warn "Could not deploy ${m_name} in ${LOCATION} (quota or model not offered here)."
    warn "  -> demos referencing ${m_name} will fall back to gpt-4o; or edit MODEL_DEPLOYMENTS / LOCATION."
  fi
done

# --- 5. Azure AI Search -----------------------------------------------------
say "Creating Azure AI Search service"
az extension add --name search --upgrade -y >/dev/null 2>&1 || true
if ! az search service show --name "${SEARCH_SERVICE}" -g "${RESOURCE_GROUP}" -o none 2>/dev/null; then
  az search service create --name "${SEARCH_SERVICE}" -g "${RESOURCE_GROUP}" \
    --sku "${SEARCH_SKU}" --location "${LOCATION}" \
    --identity-type SystemAssigned -o none
fi
ok "Search service ${SEARCH_SERVICE}"
# Prefer RBAC (the demos authenticate with DefaultAzureCredential).
az search service update --name "${SEARCH_SERVICE}" -g "${RESOURCE_GROUP}" \
  --auth-options aadOrApiKey --aad-auth-failure-mode http403 -o none 2>/dev/null || \
  warn "Could not switch Search to RBAC auth automatically — set 'Both' under Keys in the portal."
SEARCH_MI="$(az search service show --name "${SEARCH_SERVICE}" -g "${RESOURCE_GROUP}" --query identity.principalId -o tsv 2>/dev/null || true)"

# --- 6. Storage + container -------------------------------------------------
say "Creating storage account + container"
if ! az storage account show -n "${STORAGE_ACCOUNT}" -g "${RESOURCE_GROUP}" -o none 2>/dev/null; then
  az storage account create -n "${STORAGE_ACCOUNT}" -g "${RESOURCE_GROUP}" -l "${LOCATION}" \
    --sku Standard_LRS --kind StorageV2 --allow-blob-public-access false -o none
fi
ok "Storage account ${STORAGE_ACCOUNT}"
az storage container create --name "${BLOB_CONTAINER}" \
  --account-name "${STORAGE_ACCOUNT}" --auth-mode login -o none 2>/dev/null || \
  warn "Container create deferred — run infra/upload_sample_data.sh after RBAC propagates."

# --- 7. RBAC ----------------------------------------------------------------
say "Assigning RBAC roles"
USER_OID="$(az ad signed-in-user show --query id -o tsv 2>/dev/null || true)"
STORAGE_ID="$(az storage account show -n "${STORAGE_ACCOUNT}" -g "${RESOURCE_GROUP}" --query id -o tsv)"
SEARCH_ID="$(az search service show --name "${SEARCH_SERVICE}" -g "${RESOURCE_GROUP}" --query id -o tsv)"

assign() { # role  assignee-object-id  scope
  [ -n "$2" ] || return 0
  az role assignment create --role "$1" --assignee-object-id "$2" \
    --assignee-principal-type "$4" --scope "$3" -o none 2>/dev/null \
    && ok "  $1 -> ${5}" || warn "  $1 -> ${5} (already assigned or insufficient perms)"
}

# Signed-in user: use the models, drive Search, read blobs.
assign "Cognitive Services User"            "${USER_OID}" "${FOUNDRY_ID}"  "User" "you @ Foundry"
assign "Cognitive Services OpenAI User"     "${USER_OID}" "${FOUNDRY_ID}"  "User" "you @ OpenAI"
assign "Search Service Contributor"         "${USER_OID}" "${SEARCH_ID}"   "User" "you @ Search (control)"
assign "Search Index Data Contributor"      "${USER_OID}" "${SEARCH_ID}"   "User" "you @ Search (data)"
assign "Search Index Data Reader"           "${USER_OID}" "${SEARCH_ID}"   "User" "you @ Search (read)"
assign "Storage Blob Data Contributor"      "${USER_OID}" "${STORAGE_ID}"  "User" "you @ Storage"
# Search service identity: read blobs + call the embedding/LLM models (vectorizer + answer synthesis).
assign "Storage Blob Data Reader"           "${SEARCH_MI}" "${STORAGE_ID}" "ServicePrincipal" "Search MI @ Storage"
assign "Cognitive Services User"            "${SEARCH_MI}" "${FOUNDRY_ID}" "ServicePrincipal" "Search MI @ Foundry"

# --- 8. Write .env ----------------------------------------------------------
say "Writing ../.env"
ENV_FILE="${SCRIPT_DIR}/../.env"
cat > "${ENV_FILE}" <<ENV
# Auto-generated by infra/provision.sh on $(date -u +%Y-%m-%dT%H:%M:%SZ)
# ----- Foundry project (Day 1 & Day 2 SDK demos) -----
PROJECT_ENDPOINT=${PROJECT_ENDPOINT}
FOUNDRY_PROJECT_ENDPOINT=${PROJECT_ENDPOINT}
AZURE_AI_PROJECT_ENDPOINT=${PROJECT_ENDPOINT}
FOUNDRY_ACCOUNT_ENDPOINT=${FOUNDRY_ACCOUNT_ENDPOINT}

# ----- Model deployment names -----
MODEL_DEPLOYMENT_NAME=gpt-4o
AZURE_AI_MODEL_DEPLOYMENT_NAME=gpt-4o
FOUNDRY_MODEL_DEPLOYMENT_NAME=gpt-4o
PROMPT_AGENT_MODEL=gpt-5-mini
HOSTED_AGENT_MODEL=gpt-4.1
EMBEDDING_DEPLOYMENT=text-embedding-3-large

# ----- Azure AI Search (Day 2 demos 9 & 10) -----
SEARCH_ENDPOINT=${SEARCH_ENDPOINT}
AZURE_SEARCH_ENDPOINT=${SEARCH_ENDPOINT}
SEARCH_INDEX_NAME=earth-at-night
KNOWLEDGE_SOURCE_NAME=earth-at-night-ks
KNOWLEDGE_BASE_NAME=earth-at-night-kb

# ----- Storage (Earth-at-Night sample data) -----
STORAGE_ACCOUNT=${STORAGE_ACCOUNT}
BLOB_CONTAINER=${BLOB_CONTAINER}

# ----- Day 2 demo 8 (A2A): fill in after running demo8/setup_a2a_connection.sh -----
A2A_PROJECT_CONNECTION_ID=

# ----- Day 2 demo 6 (MCP): public Microsoft Learn Docs MCP server -----
MCP_SERVER_URL=https://learn.microsoft.com/api/mcp
MCP_SERVER_LABEL=mslearn
ENV
ok ".env written -> ${ENV_FILE}"

echo
ok "Provisioning complete."
say "Next:  cd ..  &&  python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
say "Then:  infra/upload_sample_data.sh   (loads Earth-at-Night docs for Day 2 retrieval demos)"
say "Run any demo, e.g.:  python day1/demo3_prompt_agent/prompt_agent.py"
