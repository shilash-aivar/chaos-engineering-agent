#!/usr/bin/env bash
# Bootstrap local chaos-agent dev dependencies (optional observability stack).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "==> Chaos Agent dev-up"
echo "    Project: $ROOT"

if [ ! -f .env ]; then
  cp .env.example .env
  echo "    Created .env from .env.example"
fi

if command -v pip3 >/dev/null 2>&1; then
  pip3 install -e ".[dev]" -q
  echo "    Python deps installed"
fi

if command -v npm >/dev/null 2>&1 && [ -d frontend ]; then
  (cd frontend && npm install --silent)
  echo "    Frontend deps installed"
fi

cat <<'EOF'

Next steps:
  Terminal 1: make dev          # API on :8000
  Terminal 2: make dev-ui       # UI on :5173

Optional (no cluster):
  export CHAOS_AGENT_SIMULATE_EXECUTION=true

CI gate locally:
  python3 scripts/ci_gate.py --pr-number 42 --files src/api/routes.py --services checkout

EOF
