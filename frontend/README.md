# Chaos Agent UI

React dashboard for the internal Chaos Engineering Agent. Most features ship as **UI previews** with static sample data — backend wiring comes over time. Pages marked **Live** call the API today.

## Navigation

### Operate (live)
- **Dashboard** (`/`) — stats, feature catalog, recent experiments
- **Experiments** (`/experiments`) — list and detail with tabs: overview, metrics, findings, approval panel
- **New experiment** (`/new`) — natural language → LLM plan → approve & run

### Intelligence (preview)
- **Infrastructure** (`/infrastructure`) — 5-ring snapshot, digital twin, blast graph
- **Remediation** (`/remediation`) — LLM findings → tickets, PRs, verify re-run
- **Chaos DNA** (`/chaos-dna`) — per-service resilience profiles and trends
- **Red vs Blue** (`/red-blue`) — campaigns (live list) + arena, transcripts (preview)

### Platform
- **Posture** (`/posture`) — gap scan (live) + bootstrap actions (preview)
- **CI gate** (`/ci-gate`) — PR resilience checks, regression suites
- **Policies** (`/policies`) — blast caps, approvals, executor allowlist, **YAML rule editor**
- **Referee** (`/referee`) — scoring weights, freeze calendar, round orchestration
- **Integrations** (`/integrations`) — Slack, GitHub, PagerDuty, Grafana, Tempo
- **Observability** (`/observability`) — steady-state guard, live metrics, deep links
- **Performance testing** (`/load-testing`) — load, stress, performance, soak scenarios paired with faults

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

Use the **context switcher** in the header to change cluster/namespace (preview — not wired to API yet).

Preview pages work without the API. Live pages need `make dev` running.

## Stack

| Layer | Technology |
|-------|------------|
| **Framework** | React 18 + Vite 5 + TypeScript 5 |
| **Routing** | React Router 6 |
| **Server state** | TanStack Query 5 (polling, cache, mutations) |
| **Client state** | Zustand (cluster/namespace context) |
| **API** | Axios → `/api` proxy → FastAPI `:8000` |
| **Styling** | Tailwind CSS v4 |
| **UI** | Radix primitives + CVA (shadcn-style) + lucide-react |
| **Charts** | Recharts (metrics) · d3 (topology graphs, preview) |
| **Toasts** | Sonner |
| **Live updates** | TanStack Query `refetchInterval` (WebSocket planned) |

## Design

Mission-control aesthetic for internal SRE teams — inspired by Grafana / Linear / kubemigrate:

- **Plus Jakarta Sans** + **JetBrains Mono** (IDs, metrics)
- **Amber** primary (chaos brand) — not generic purple-on-dark
- Subtle mesh background, elevated surfaces, data tables
- Status dots with pulse for active runs
- TanStack Query for live data; Recharts for metrics

Preview pages (`/demo`, `/roadmap`) remain for walkthroughs but are no longer the dashboard focus.
