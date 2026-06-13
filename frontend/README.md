# Chaos Agent UI

React dashboard for the internal Chaos Engineering Agent. Most features ship as **UI previews** with static sample data — backend wiring comes over time. Pages marked **Live** call the API today.

## Navigation

### Operate (live)
- **Dashboard** (`/`) — stats, feature catalog, recent experiments
- **Experiments** (`/experiments`) — list and detail with timeline + abort
- **New experiment** (`/new`) — natural language → LLM plan → approve & run

### Intelligence (preview)
- **Infrastructure** (`/infrastructure`) — 5-ring snapshot, digital twin, blast graph
- **Remediation** (`/remediation`) — LLM findings → tickets, PRs, verify re-run
- **Chaos DNA** (`/chaos-dna`) — per-service resilience profiles and trends
- **Red vs Blue** (`/red-blue`) — campaigns (live list) + arena, transcripts (preview)

### Platform
- **Posture** (`/posture`) — gap scan (live) + bootstrap actions (preview)
- **CI gate** (`/ci-gate`) — PR resilience checks, regression suites
- **Policies** (`/policies`) — blast caps, approvals, executor allowlist
- **Integrations** (`/integrations`) — Slack, GitHub, PagerDuty, Grafana, Tempo
- **Observability** (`/observability`) — steady-state guard, live metrics, deep links
- **Load testing** (`/load-testing`) — k6 scenarios paired with faults

### Vision
- **UI walkthrough** (`/demo`) — end-to-end flow in one page
- **Roadmap** (`/roadmap`) — phases 1–4 + future features

## Dev

```bash
# Terminal 1 — API
cd ..
make dev

# Terminal 2 — UI
npm install
npm run dev
```

UI: http://localhost:5173 (proxies `/api` → `http://localhost:8000`)

Preview pages work without the API. Live pages need `make dev` running.

## Stack

React 18 · Vite · TypeScript · Tailwind v4 · React Router · Zustand · Axios
