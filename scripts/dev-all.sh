#!/usr/bin/env bash
# Start API + UI together. Run from repo root: ./scripts/dev-all.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

export PYTHONPATH=src
export CHAOS_AGENT_SIMULATE_EXECUTION="${CHAOS_AGENT_SIMULATE_EXECUTION:-true}"

echo "Starting API on http://localhost:8000"
python3 -m uvicorn chaos_agent.api.app:create_app --factory --reload --host 0.0.0.0 --port 8000 &
API_PID=$!

cleanup() {
  kill "$API_PID" 2>/dev/null || true
}
trap cleanup EXIT

sleep 2
if ! curl -sf http://localhost:8000/health >/dev/null; then
  echo "API failed to start — run: make dev (see traceback above)"
  exit 1
fi

echo "Starting UI on http://localhost:5173"
cd frontend && npm run dev
