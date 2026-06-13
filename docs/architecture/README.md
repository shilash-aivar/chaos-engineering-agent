# Architecture

## Layers

| Layer | Package | Responsibility |
|-------|---------|----------------|
| Orchestration | `orchestrator`, `api`, `workers` | Experiment lifecycle, async jobs, audit |
| Intelligence | `composer`, `red`, `blue`, `remediator` | LLM planning, adversarial agents, fixes |
| Execution | `executors` | Chaos Mesh, AWS FIS, Toxiproxy, k6 |
| Layer | Package | Responsibility |
|-------|---------|----------------|
| Ground truth | `collectors`, `graph` | K8s, AWS, **app**, **deps**, **observability** → unified snapshot |
| Safety | `referee`, `orchestrator/guards` | Blast radius, freeze windows, scoring |
| Integrations | `integrations` | Slack, GitHub, anchor context |

## Experiment lifecycle

```
pending → simulating → awaiting_approval → running → aborting → complete | failed
```

## Core schemas

- `schemas/experiment_plan.json` — input to executors
- `schemas/finding.json` — remediation output
- `schemas/infra_snapshot.json` — collectors output
- `schemas/round_score.json` — Red/Blue referee output

## Data flow

```
collectors → graph + posture
                ↓
         composer (human/LLM) → ExperimentPlan
                ↓
         referee (validate) → orchestrator → executors
                ↓
         metrics + audit → remediator → GitHub/runbooks
                ↓
         red/blue scores → regression suites
```
