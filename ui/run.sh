#!/usr/bin/env bash
# Launch the Foundry Live Demo Console (macOS / Linux / WSL).
#   ./ui/run.sh                 # http://127.0.0.1:8099
# Requires: az login + a populated ../.env (run infra/provision.sh first).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PORT="${PORT:-8099}"
PY="$ROOT/.venv/bin/python"
[ -x "$PY" ] || PY="$ROOT/.venv/Scripts/python.exe"
[ -x "$PY" ] || PY="python"
echo "Foundry Live Demo Console -> http://127.0.0.1:$PORT"
cd "$ROOT"
exec "$PY" -m uvicorn ui.server.main:app --host 127.0.0.1 --port "$PORT"
