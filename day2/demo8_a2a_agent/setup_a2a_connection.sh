#!/usr/bin/env bash
# Day 2 · Demo 8 — create the A2A project connection that a2a_agent.py needs.
#
# An A2A connection points your Foundry project at a *secondary* A2A-compatible
# agent endpoint (its agent card / base URL). Set A2A_TARGET_URL to that
# endpoint before running, e.g. another Foundry agent published with A2A, a
# Fabric Data Agent, or any A2A server.
#
# Usage:
#   A2A_TARGET_URL="https://my-secondary-agent.example.com/a2a" ./setup_a2a_connection.sh
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../../infra/00-variables.sh"

A2A_TARGET_URL="${A2A_TARGET_URL:-}"
CONNECTION_NAME="${CONNECTION_NAME:-a2a-secondary-agent}"
API_VERSION="${PROJECTS_API_VERSION:-2025-06-01}"

[ -n "${A2A_TARGET_URL}" ] || die "Set A2A_TARGET_URL to your secondary agent's A2A endpoint first."
[ -n "${SUBSCRIPTION_ID}" ] || die "Run 'az login' first."

FOUNDRY_ID="$(az cognitiveservices account show -n "${FOUNDRY_ACCOUNT}" -g "${RESOURCE_GROUP}" --query id -o tsv)"
CONN_URL="https://management.azure.com${FOUNDRY_ID}/projects/${FOUNDRY_PROJECT}/connections/${CONNECTION_NAME}?api-version=${API_VERSION}"

say "Creating A2A connection '${CONNECTION_NAME}' -> ${A2A_TARGET_URL}"
if az rest --method put --url "${CONN_URL}" --headers "Content-Type=application/json" --body "{
  \"properties\": {
    \"category\": \"A2A\",
    \"target\": \"${A2A_TARGET_URL}\",
    \"authType\": \"None\",
    \"isSharedToAll\": false,
    \"metadata\": { \"purpose\": \"Accelerate Agentic AI demo 8\" }
  }
}" -o none 2>/dev/null; then
  CONN_ID="${FOUNDRY_ID}/projects/${FOUNDRY_PROJECT}/connections/${CONNECTION_NAME}"
  ok "A2A connection created."
  echo
  echo "Add this to ../../.env :"
  echo "  A2A_PROJECT_CONNECTION_ID=${CONN_ID}"
else
  warn "REST create failed (preview api-version churns, or auth type differs for your endpoint)."
  warn "Create the connection in the Foundry portal: Project > Connected resources > + > A2A,"
  warn "then copy its resource ID into ../../.env as A2A_PROJECT_CONNECTION_ID."
fi
