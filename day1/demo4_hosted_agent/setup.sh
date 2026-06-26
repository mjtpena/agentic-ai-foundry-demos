#!/usr/bin/env bash
# Day 1 · Demo 4 — provision + locally test + deploy a hosted agent with azd.
# Mirrors slide 87 step-by-step. Run from this folder.
set -euo pipefail
command -v azd >/dev/null 2>&1 || { echo "Azure Developer CLI (azd) required: https://aka.ms/azd-install"; exit 1; }

echo "==> Step 1: install the AI agent extension for azd"
azd ext install azure.ai.agents || true
azd ext list | grep -i agent || true

echo "==> Step 2: initialise the project (interactive) — pick 'Start new from a template'"
echo "    You'll choose: environment name, subscription, location (australiaeast),"
echo "    model SKU, deployment name (use gpt-4.1), and container size."
azd ai agent init

echo "==> Step 3: provision the Azure resources for the hosted agent"
azd provision

echo "==> Step 4: run locally and smoke-test on :8088"
echo "    In THIS terminal:  azd ai agent run"
echo "    In ANOTHER terminal: azd ai agent invoke --local \"What time is it in Tokyo?\""
echo
echo "==> Step 5: deploy to Foundry Agent Service (container built remotely; no Docker needed)"
echo "    azd deploy"
echo "    azd ai agent show       # verify status"
echo "    azd ai agent invoke \"How many hours until 9am in London?\""
echo "    azd ai agent monitor    # live logs"
echo
echo "Clean up when finished (charges accrue while deployed):  azd down"
