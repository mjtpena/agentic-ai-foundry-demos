#!/usr/bin/env bash
# Loads the NASA "Earth at Night" sample documents into the blob container that
# backs the Day 2 agentic-retrieval demos (knowledge source 'earth-at-night-ks').
# These are the exact docs the Day 2 demo + Microsoft Learn quickstart use.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/00-variables.sh"

SAMPLE_DIR="$(mktemp -d)"
REPO_RAW="https://raw.githubusercontent.com/Azure-Samples/azure-search-sample-data/main/nasa-e-book/earth-at-night-json"

say "Downloading Earth-at-Night sample documents"
# The sample set ships as a single documents.json array; pull it and split.
if curl -fsSL "${REPO_RAW}/documents.json" -o "${SAMPLE_DIR}/documents.json"; then
  ok "Downloaded documents.json"
else
  warn "Could not fetch sample data automatically."
  warn "Manually download from https://github.com/Azure-Samples/azure-search-sample-data"
  warn "(nasa-e-book/earth-at-night-json) and upload to container '${BLOB_CONTAINER}'."
  exit 0
fi

say "Uploading to ${STORAGE_ACCOUNT}/${BLOB_CONTAINER}"
az storage blob upload-batch \
  --account-name "${STORAGE_ACCOUNT}" \
  --destination "${BLOB_CONTAINER}" \
  --source "${SAMPLE_DIR}" \
  --pattern "*.json" \
  --auth-mode login --overwrite -o none
ok "Sample data uploaded. The Day 2 knowledge source can now index it."
rm -rf "${SAMPLE_DIR}"
