#!/usr/bin/env bash
# =============================================================================
# Accelerate Agentic AI — shared configuration
# Sourced by every provisioning / per-demo script. Edit values here ONCE.
# =============================================================================

# --- Naming -----------------------------------------------------------------
# A short, lowercase, unique-ish suffix keeps globally-scoped names (storage,
# search, Foundry account) from colliding. Override by exporting SUFFIX first.
export SUFFIX="${SUFFIX:-$(echo "${USER:-aa}$(date +%y%m%d)" | tr -cd 'a-z0-9' | cut -c1-8)}"

export LOCATION="${LOCATION:-australiaeast}"          # chosen for this workshop
export RESOURCE_GROUP="${RESOURCE_GROUP:-rg-agentic-ai-demos}"

# Foundry (Microsoft Foundry / Azure AI Services account + project)
export FOUNDRY_ACCOUNT="${FOUNDRY_ACCOUNT:-foundry-aa-${SUFFIX}}"   # 2-64 chars
export FOUNDRY_PROJECT="${FOUNDRY_PROJECT:-agentic-demos}"

# Azure AI Search (used by Day 2 agentic retrieval demos 9 & 10)
export SEARCH_SERVICE="${SEARCH_SERVICE:-srch-aa-${SUFFIX}}"        # 2-60 chars, global
export SEARCH_SKU="${SEARCH_SKU:-basic}"                            # basic supports semantic ranker

# Storage (blob container that backs the Earth-at-Night knowledge source)
export STORAGE_ACCOUNT="${STORAGE_ACCOUNT:-staa${SUFFIX}}"          # 3-24 chars, global, lowercase
export BLOB_CONTAINER="${BLOB_CONTAINER:-earth-at-night-data}"

# --- Model deployments ------------------------------------------------------
# "name:format:version:sku:capacity"  (capacity = thousands of TPM)
# Edit freely. If a model/version isn't offered in $LOCATION the script will
# warn and continue; gpt-4o is the universal fallback every demo can use.
export MODEL_DEPLOYMENTS=(
  "gpt-4o:OpenAI:2024-11-20:GlobalStandard:30"
  "gpt-4.1:OpenAI:2025-04-14:GlobalStandard:30"
  "gpt-4.1-mini:OpenAI:2025-04-14:GlobalStandard:30"
  "gpt-5-mini:OpenAI::GlobalStandard:30"
  "text-embedding-3-large:OpenAI:1:Standard:50"
)

# Management API version used for the Foundry *project* sub-resource.
# Bump this if Microsoft updates the projects API and creation 400s.
export PROJECTS_API_VERSION="${PROJECTS_API_VERSION:-2025-06-01}"

# --- Derived (do not edit) --------------------------------------------------
export SUBSCRIPTION_ID="${SUBSCRIPTION_ID:-$(az account show --query id -o tsv 2>/dev/null)}"

# New-Foundry project endpoint shape: https://<account>.services.ai.azure.com/api/projects/<project>
export PROJECT_ENDPOINT="https://${FOUNDRY_ACCOUNT}.services.ai.azure.com/api/projects/${FOUNDRY_PROJECT}"
export FOUNDRY_ACCOUNT_ENDPOINT="https://${FOUNDRY_ACCOUNT}.services.ai.azure.com"
export SEARCH_ENDPOINT="https://${SEARCH_SERVICE}.search.windows.net"

# Pretty logging helpers ------------------------------------------------------
c_reset=$'\e[0m'; c_blue=$'\e[1;34m'; c_green=$'\e[1;32m'; c_yellow=$'\e[1;33m'; c_red=$'\e[1;31m'
say()  { printf '%s\n' "${c_blue}==>${c_reset} $*"; }
ok()   { printf '%s\n' "${c_green}  ✓${c_reset} $*"; }
warn() { printf '%s\n' "${c_yellow}  ! ${c_reset}$*"; }
die()  { printf '%s\n' "${c_red}  ✗ $*${c_reset}" >&2; exit 1; }
