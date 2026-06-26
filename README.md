# Chaos Engineering Agent

Internal AI-driven resilience platform for Kubernetes and AWS.

**Core loop:** infra snapshot → human/LLM scenarios → safe fault injection → LLM remediation → Red vs Blue scoring → verify.

## Directory layout

```
chaos-engineering-agent/
├── config/                 # Runtime and resilience policy YAML
├── deploy/                 # kind, Helm, Terraform
├── docs/                   # Architecture and runbooks
├── schemas/                # JSON schemas (ExperimentPlan, Finding, InfraSnapshot)
├── frontend/               # React dashboard (Vite + Tailwind)
├── scripts/                # Dev and bootstrap scripts
├── src/chaos_agent/        # Main Python package
│   ├── api/                # FastAPI REST + WebSocket
│   ├── bootstrap/          # Optional installers (Istio, Chaos Mesh, etc.)
│   ├── blue/               # Defender agent — hardening proposals
│   ├── cli/                # `chaos` CLI (Typer)
│   ├── collectors/         # K8s, AWS, Istio, Prometheus readers
│   ├── composer/           # Human + LLM scenario → ExperimentPlan
│   ├── executors/          # Chaos Mesh, AWS FIS, Toxiproxy, k6
│   ├── graph/              # Unified dependency graph (NetworkX)
│   ├── integrations/       # Slack, GitHub, anchor, PagerDuty
│   ├── models/             # Pydantic domain models
│   ├── orchestrator/       # State machine, guards, rollback
│   ├── posture/            # K8s + AWS resilience rules engine
│   ├── red/                # Breaker agent — attack planner + scoring input
│   ├── referee/            # Blast caps, freeze calendar, round orchestration
│   ├── remediator/         # LLM findings → tickets, runbooks, PR drafts
│   ├── storage/            # PostgreSQL, Redis, migrations
│   └── workers/            # Celery async jobs
└── tests/
```

## Quick start

Requires [uv](https://docs.astral.sh/uv/) (Python 3.12). Dependencies are locked in `uv.lock`.

```bash
cp .env.example .env
make install   # uv sync --extra dev + npm install

# Terminal 1 — API
make dev

# Terminal 2 — UI
make dev-ui
```

- API: http://localhost:8000
- UI: http://localhost:5173

```bash
chaos --help
chaos status
chaos run "pod kill on checkout during load"
```

## Python & dependencies (uv)

This project uses [uv](https://docs.astral.sh/uv/) instead of `requirements.txt`. Python version and packages are pinned so you avoid mismatches like `str | None` errors on older interpreters or different dependency sets across machines.

| File | Purpose |
|------|---------|
| `.python-version` | Pins **Python 3.12** for local dev |
| `pyproject.toml` | Declares dependencies (`requires-python >= 3.10`) |
| `uv.lock` | Locked, reproducible installs (commit this file) |
| `.venv/` | Local virtualenv created by uv (gitignored) |

**Use these commands** — they run inside the uv-managed `.venv`:

```bash
uv sync --extra dev    # install / update deps from uv.lock
uv run pytest tests/   # run tests
make install           # uv sync + npm install
make test              # full test suite
make dev               # API server
make lock              # regenerate uv.lock after changing pyproject.toml
```

`make install` is the single entry point on a fresh machine — it runs `uv python install 3.12` first, so you don't need Python 3.12 preinstalled.

CI uses `uv sync --frozen`, so builds fail if `uv.lock` is out of date with `pyproject.toml`.

**Avoid** running bare `python`, `pip install`, or `pytest` outside uv — that can pick up the wrong system Python (e.g. 3.9) or an unmigrated global environment. Stick to `uv run …` or the `make` targets above.

## Frontend screens

| Route | Purpose |
|-------|---------|
| `/` | Dashboard — stats, recent runs, Red/Blue, posture gaps |
| `/experiments` | Experiment list and detail |
| `/new` | NL scenario → LLM plan → approve & run |
| `/posture` | K8s + AWS + **app** + **deps** + **observability** posture scan |
| `/red-blue` | Adversarial campaign scoreboard |

## Phase 1 orchestrator (implemented)

- **State machine:** `pending → running → aborting → complete | failed`
- **Chaos Mesh:** `pod_kill`, `network_latency` CRDs with idempotent rollback
- **Steady-state guard:** Prometheus baseline + auto-abort on 2× error / 3× latency
- **Safety validator:** blast radius cap, prod gate, required watch metrics
- **Storage:** SQLite audit trail + timeline events
- **Simulation mode:** set `CHAOS_AGENT_SIMULATE_EXECUTION=true` when K8s/Prom unavailable

```bash
# Force simulation (no cluster required)
export CHAOS_AGENT_SIMULATE_EXECUTION=true
make dev
```

## Target rings (no GCP/Azure)

| Ring | What |
|------|------|
| **K8s + AWS** | Chaos Mesh, FIS (later), RDS, SQS, probes |
| **Application** | Circuit breakers, retries, feature flags |
| **Dependencies** | Postgres, Redis, Kafka, Stripe, Auth0 via Toxiproxy |
| **Observability** | Prometheus, Grafana, Tempo, PagerDuty, GitHub |

```bash
GET /snapshot       # unified dependency graph
GET /posture/scan   # posture gaps across all rings
```

## Phases

| Phase | Focus |
|-------|--------|
| 1 | **Done (v0.1)** — Orchestrator, Chaos Mesh executor, Prometheus guard, rollback, SQLite audit |
| 2 | LLM composer + remediation + posture rules |
| 3 | Red agent + PR-scoped CI + AWS FIS |
| 4 | Blue agent + closed-loop campaigns in staging |

## Safety defaults

- Staging-only unless `CHAOS_ALLOW_PROD=true` + Slack approval
- Max 30% replica blast radius
- Steady-state auto-abort: 2× error rate, 3× latency vs baseline
- AWS changes via Terraform PR — no live mutations in v1

## Reference

See `Chaos_Engineering_Agent_Final (2).pdf` and `docs/architecture/` for full vision.
