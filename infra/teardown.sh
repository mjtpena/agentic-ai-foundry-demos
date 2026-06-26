#!/usr/bin/env bash
# Deletes the entire resource group and everything in it. The slides' "Clean up
# resources" step. Stops all charges. There is no undo.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/00-variables.sh"
say "This will DELETE resource group '${RESOURCE_GROUP}' and all resources in it."
read -r -p "Type the resource group name to confirm: " confirm
[ "${confirm}" = "${RESOURCE_GROUP}" ] || die "Name mismatch — aborted."
az group delete -n "${RESOURCE_GROUP}" --yes --no-wait
ok "Deletion started (running in background). Verify in the portal."
