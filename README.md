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

```bash
cp .env.example .env
pip install -e ".[dev]"
make dev
```

```bash
chaos --help
chaos status
chaos run "pod kill on checkout during load"
```

## Phases

| Phase | Focus |
|-------|--------|
| 1 | Safe execute: guard, rollback, Chaos Mesh, audit |
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
