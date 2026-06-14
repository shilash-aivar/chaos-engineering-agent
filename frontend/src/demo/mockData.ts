/** Static sample data for UI preview sections — backend wiring comes later */

import type {
  ChaosDnaProfile,
  ChaosLoadPairing,
  IntegrationConfig,
  LoadTestScenario,
  LoadTestType,
  LoadTestTypeInfo,
  ProductFeature,
  RegressionSuite,
  RemediationFinding,
  RoadmapPhase,
  SafetyPolicy,
} from '@/types'

export const demoStats = {
  experiments_total: 47,
  experiments_running: 2,
  avg_resilience_score: 73,
  posture_gaps: 8,
  teams_active: 6,
  regressions_passing: 12,
}

export const demoScenario = {
  userPrompt: 'Test what happens if the payments DB loses connectivity during checkout peak traffic',
  plan: {
    name: 'checkout-payments-db-blackhole',
    hypothesis: 'Checkout SLO breaches when payments RDS is unreachable under load',
    faults: [
      { executor: 'chaos_mesh', type: 'network_latency', target: 'payments-api', detail: '500ms latency' },
      { executor: 'toxiproxy', type: 'dependency_blackhole', target: 'payments-db', detail: 'TCP blackhole 60s' },
      { executor: 'k6', type: 'load', target: 'checkout', detail: '120 VUs, 5 min' },
    ],
    infra_evidence: [
      'checkout → payments-api: no circuit breaker (Istio VS)',
      'RDS payments-db: Multi-AZ disabled',
      'payments-api: PriorityClass not set — evicted first under pressure',
    ],
    blast_radius: 'staging · max 30% replicas · single namespace',
  },
  preMortem:
    'Expect checkout error rate to spike within 45s. p99 latency may exceed 2s. Blast likely propagates to order-events SQS. Escape hatch: auto-rollback on 2× error rate.',
}

export const demoTimeline = [
  { at: '14:02:01', event: 'Digital twin simulation', detail: '847 paths analyzed · 12% failure probability', status: 'done' },
  { at: '14:02:45', event: 'Baseline captured', detail: 'error_rate=0.08% · p99=210ms', status: 'done' },
  { at: '14:03:12', event: 'Fault injected', detail: 'DB blackhole + 500ms upstream latency', status: 'done' },
  { at: '14:03:58', event: 'SLO breach', detail: 'error_rate 0.08% → 4.6%', status: 'alert' },
  { at: '14:04:02', event: 'Auto rollback', detail: 'Chaos CRDs deleted · metrics recovering', status: 'done' },
  { at: '14:05:30', event: 'LLM remediation', detail: '3 findings · 3 GitHub issues created', status: 'active' },
]

export const demoMetrics = [
  { label: 'Error rate', unit: '%', baseline: 0.08, current: 4.6, threshold: 0.16 },
  { label: 'p99 latency', unit: 'ms', baseline: 210, current: 1840, threshold: 630 },
  { label: 'DB connections', unit: '', baseline: 42, current: 98, threshold: 84 },
  { label: 'SQS age', unit: 's', baseline: 2, current: 47, threshold: 10 },
]

export const demoTopology = {
  nodes: [
    { id: 'ingress', label: 'ALB', tier: 'infra', x: 50, y: 8 },
    { id: 'checkout', label: 'checkout', tier: 'critical', x: 50, y: 28 },
    { id: 'payments', label: 'payments-api', tier: 'critical', x: 25, y: 52 },
    { id: 'stripe-api', label: 'stripe-api', tier: 'deps', x: 10, y: 52 },
    { id: 'auth0', label: 'auth0', tier: 'deps', x: 90, y: 52 },
    { id: 'rds', label: 'payments-db', tier: 'data', x: 25, y: 76 },
    { id: 'sqs', label: 'order-events', tier: 'standard', x: 75, y: 76 },
  ],
  edges: [
    { from: 'ingress', to: 'checkout' },
    { from: 'checkout', to: 'payments' },
    { from: 'checkout', to: 'auth0' },
    { from: 'payments', to: 'rds' },
    { from: 'payments', to: 'stripe-api' },
    { from: 'checkout', to: 'sqs' },
  ],
  blastPath: ['checkout', 'payments', 'rds'],
}

export const demoRedBlue = {
  campaign: 'checkout-launch-game-day',
  round: 2,
  maxRounds: 3,
  redScore: 68,
  blueScore: 54,
  rounds: [
    { round: 1, red: 72, blue: 41, attack: 'inventory timeout + traffic spike', defense: 'Added readiness probe' },
    { round: 2, red: 68, blue: 54, attack: 'DB blackhole during load', defense: 'RDS Multi-AZ PR opened' },
    { round: 3, red: null, blue: null, attack: 'AZ impairment + pod kill (planned)', defense: '—' },
  ],
}

export const demoRedBlueTranscript = {
  red: [
    { role: 'red', text: 'Targeting payments-db blackhole during k6 load on checkout — exploit missing circuit breaker.' },
    { role: 'red', text: 'Injected toxiproxy timeout on payments-db TCP. Error rate climbing.' },
    { role: 'red', text: 'SLO breached in 46s. Score +68 for cascading failure.' },
  ],
  blue: [
    { role: 'blue', text: 'Detected pool exhaustion. Opening PR to increase connection pool 10→25.' },
    { role: 'blue', text: 'Drafting Istio VirtualService retry policy for checkout→payments.' },
    { role: 'blue', text: 'Terraform PR #1844 opened: enable Multi-AZ on payments-db.' },
  ],
  referee: 'Round 2: Red 68 · Blue 54. Blue gains ground on infra fixes; Red wins on time-to-breach.',
}

export const demoFindings = [
  {
    id: 'F1',
    severity: 'critical' as const,
    title: 'DB connection pool exhausted in 12s',
    prescription: 'Increase pool 10→25. Add 3s connection timeout.',
    ticket: '#1842',
    scope: 'k8s',
  },
  {
    id: 'F2',
    severity: 'critical' as const,
    title: 'No circuit breaker on payments API',
    prescription: 'Add retry: attempts=3, perTryTimeout=2s on Istio VS.',
    ticket: '#1843',
    scope: 'mesh',
  },
  {
    id: 'F3',
    severity: 'high' as const,
    title: 'RDS single-AZ',
    prescription: 'Terraform PR: enable Multi-AZ on payments-db.',
    ticket: '#1844',
    scope: 'aws',
  },
  {
    id: 'F4',
    severity: 'high' as const,
    title: 'Tempo trace gap on checkout→payments',
    prescription: 'Add OTel span on outbound HTTP client; export to Tempo.',
    ticket: '#1845',
    scope: 'observability',
  },
]

export const demoRemediationPipeline: RemediationFinding[] = [
  { id: 'F1', severity: 'critical', title: 'DB connection pool exhausted in 12s', prescription: 'Increase pool 10→25', ticket: '#1842', scope: 'k8s', status: 'in_progress', experiment_id: 'exp-checkout-001' },
  { id: 'F2', severity: 'critical', title: 'No circuit breaker on payments API', prescription: 'Istio VS retry policy', pr: 'platform/istio-checkout#91', scope: 'mesh', status: 'open', experiment_id: 'exp-checkout-001' },
  { id: 'F3', severity: 'high', title: 'RDS single-AZ', prescription: 'Terraform Multi-AZ', pr: 'infra/terraform#1844', scope: 'aws', status: 'in_progress', experiment_id: 'exp-checkout-001' },
  { id: 'F5', severity: 'medium', title: 'Missing PriorityClass on payments-api', prescription: 'Create chaos-critical PriorityClass', ticket: '#1850', scope: 'k8s', status: 'verified', experiment_id: 'exp-payments-002' },
  { id: 'F6', severity: 'low', title: 'SQS DLQ not configured', prescription: 'Add DLQ + alarm', pr: 'infra/terraform#1851', scope: 'aws', status: 'closed', experiment_id: 'exp-events-003' },
]

export const demoScoreHistory = [
  { week: 'W1', score: 58 },
  { week: 'W2', score: 61 },
  { week: 'W3', score: 64 },
  { week: 'W4', score: 67 },
  { week: 'W5', score: 69 },
  { week: 'W6', score: 73 },
]

export const demoPrComment = `## Chaos Agent — PR resilience check

| Metric | Before | After | Delta |
|--------|--------|-------|-------|
| Resilience score | 71 | 68 | -3 |
| checkout pod_kill | pass | pass | — |
| payments DB failover | pass | **fail** | new regression |

**Red agent** ran 2 targeted faults on \`payments-api\` (changed in this PR).

> Recommendation: merge only after Blue PR #1844 (Multi-AZ) lands or waive with platform approval.`

export const demoInfraRings = {
  k8s: {
    cluster: 'eks-staging',
    namespaces: ['staging', 'platform'],
    deployments: 24,
    services: 18,
    chaos_mesh: 'installed',
    istio: 'partial',
    items: [
      { name: 'checkout', detail: 'replicas=3 · probes=readiness only', status: 'gap' },
      { name: 'payments-api', detail: 'replicas=2 · probes=none', status: 'gap' },
      { name: 'inventory-api', detail: 'replicas=2 · PriorityClass=standard', status: 'ok' },
    ],
  },
  aws: {
    account: '111122223333',
    region: 'us-east-1',
    items: [
      { name: 'payments-db', detail: 'RDS PostgreSQL · multi_az=false', status: 'gap' },
      { name: 'order-events', detail: 'SQS · no DLQ', status: 'gap' },
      { name: 'checkout-alb', detail: 'ALB · WAF enabled', status: 'ok' },
      { name: 'session-cache', detail: 'ElastiCache Redis · cluster mode', status: 'ok' },
    ],
  },
  app: {
    items: [
      { name: 'checkout', detail: 'CB=false · retry=false · flags: checkout-v2', status: 'gap' },
      { name: 'payments-api', detail: 'CB=false · retry=true · stripe-fallback', status: 'gap' },
      { name: 'inventory-api', detail: 'CB=true · retry=true', status: 'ok' },
    ],
  },
  deps: {
    items: [
      { name: 'payments-db', detail: 'postgres · owner=payments-api', status: 'gap' },
      { name: 'stripe-api', detail: 'http · 3rd party · timeout=true', status: 'ok' },
      { name: 'auth0', detail: 'http · 3rd party · timeout=true', status: 'ok' },
      { name: 'fulfillment-kafka', detail: 'kafka · owner=order-events', status: 'ok' },
    ],
  },
  observability: {
    items: [
      { name: 'prometheus', detail: 'Scraping 42 targets', status: 'ok' },
      { name: 'grafana', detail: 'Chaos dashboards provisioned', status: 'ok' },
      { name: 'tempo', detail: 'Missing span on checkout→payments', status: 'gap' },
      { name: 'pagerduty', detail: '3 recent incidents correlated', status: 'ok' },
      { name: 'github', detail: 'Remediation issues auto-created', status: 'ok' },
    ],
  },
}

export const demoChaosDna: ChaosDnaProfile[] = [
  { service: 'checkout', tier: 'critical', resilience_score: 62, faults_survived: ['pod_kill', 'network_latency'], weak_points: ['payments dependency', 'no circuit breaker'], last_tested: '2d ago', trend: 'up' },
  { service: 'payments-api', tier: 'critical', resilience_score: 54, faults_survived: ['pod_kill'], weak_points: ['RDS single-AZ', 'pool size'], last_tested: '1d ago', trend: 'flat' },
  { service: 'inventory-api', tier: 'standard', resilience_score: 81, faults_survived: ['pod_kill', 'timeout', 'latency', 'traffic_spike'], weak_points: ['upstream cache cold start'], last_tested: '5d ago', trend: 'up' },
  { service: 'order-events', tier: 'standard', resilience_score: 71, faults_survived: ['sqs_delay'], weak_points: ['no DLQ'], last_tested: '3d ago', trend: 'down' },
]

export const demoPolicies: SafetyPolicy[] = [
  { id: 'env', name: 'Environment gate', value: 'staging only', enforced: true, description: 'Production requires CHAOS_ALLOW_PROD + Slack approval' },
  { id: 'blast', name: 'Max replica blast', value: '30%', enforced: true, description: 'Hard cap on affected replicas per experiment' },
  { id: 'abort', name: 'Steady-state auto-abort', value: '2× error · 3× latency', enforced: true, description: 'Prometheus guard triggers rollback' },
  { id: 'ttl', name: 'Rollback TTL', value: '300s', enforced: true, description: 'Safety net deletes Chaos CRDs after TTL' },
  { id: 'executors', name: 'Executor allowlist', value: 'chaos_mesh, toxiproxy, k6', enforced: true, description: 'aws_fis disabled until Phase 3' },
  { id: 'freeze', name: 'Freeze windows', value: 'Fri 16:00–Mon 08:00 UTC', enforced: false, description: 'Block experiments during change freeze' },
  { id: 'approval', name: 'Human approval', value: 'prod + cross-namespace', enforced: true, description: 'awaiting_approval state before inject' },
]

export const demoIntegrations: IntegrationConfig[] = [
  { id: 'slack', name: 'Slack', type: 'slack', status: 'planned', detail: '#chaos-agent-approvals', events: ['prod approval', 'SLO breach', 'campaign complete'] },
  { id: 'github', name: 'GitHub', type: 'github', status: 'connected', detail: 'platform/checkout', events: ['remediation issues', 'CI gate comments', 'Terraform PRs'] },
  { id: 'pagerduty', name: 'PagerDuty', type: 'pagerduty', status: 'connected', detail: 'Platform on-call', events: ['incident correlation', 'experiment context'] },
  { id: 'prometheus', name: 'Prometheus', type: 'prometheus', status: 'connected', detail: 'http://prometheus:9090', events: ['baseline', 'steady-state guard', 'SLO breach'] },
  { id: 'grafana', name: 'Grafana', type: 'grafana', status: 'connected', detail: 'Chaos experiment dashboards', events: ['live panels', 'post-run reports'] },
  { id: 'tempo', name: 'Tempo', type: 'tempo', status: 'connected', detail: 'Trace correlation', events: ['fault window traces', 'blast path analysis'] },
]

export const demoRegressionSuites: RegressionSuite[] = [
  { id: 'rb-checkout', name: 'checkout-launch-game-day R3', source: 'red_blue', tests: 8, passing: 7, last_run: '1d ago' },
  { id: 'exp-payments', name: 'payments-db-blackhole', source: 'experiment', tests: 5, passing: 4, last_run: '2d ago' },
  { id: 'ci-pr-892', name: 'PR #892 payments-api', source: 'manual', tests: 3, passing: 2, last_run: '4h ago' },
]

export const loadTestTypes: LoadTestTypeInfo[] = [
  {
    type: 'load',
    title: 'Load test',
    question: 'Does it handle expected peak traffic?',
    description: 'Sustain realistic concurrent users at production-like volume. Validates SLOs under normal high traffic.',
    when_to_use: 'Before launches, after scaling changes, baseline regression',
    typical_duration: '5–15 min',
    chaos_pairing: 'Run steady load while injecting latency or partial outages',
  },
  {
    type: 'stress',
    title: 'Stress test',
    question: 'Where does it break?',
    description: 'Ramp VUs beyond expected capacity until errors or latency cliff. Finds the breaking point and degradation curve.',
    when_to_use: 'Capacity planning, autoscaling validation, Red agent attacks',
    typical_duration: '10–20 min (ramp to failure)',
    chaos_pairing: 'Increase load until fault triggers cascade — measures blast under pressure',
  },
  {
    type: 'performance',
    title: 'Performance test',
    question: 'How fast is it under light load?',
    description: 'Low concurrency focused on latency percentiles (p50, p95, p99) and throughput — not max capacity.',
    when_to_use: 'After code changes, dependency upgrades, mesh config tweaks',
    typical_duration: '3–5 min',
    chaos_pairing: 'Baseline perf first, then re-run with fault to measure regression',
  },
  {
    type: 'soak',
    title: 'Soak test',
    question: 'Does it survive over time?',
    description: 'Moderate load for extended duration. Surfaces memory leaks, connection pool exhaustion, queue backlog growth.',
    when_to_use: 'Nightly staging, pre game-day, after pool/timeout config changes',
    typical_duration: '1–4 hours',
    chaos_pairing: 'Long-running load + intermittent faults (pod kill, network blips)',
  },
]

export const demoLoadTests: LoadTestScenario[] = [
  {
    id: 'checkout-peak',
    name: 'Checkout peak traffic',
    type: 'load',
    target: 'checkout',
    vus: 120,
    duration: '5m',
    ramp: '30s',
    goal: 'Sustain Black Friday peak — error rate < 0.5%, p99 < 500ms',
    stages: [
      { duration: '30s', target: 120 },
      { duration: '5m', target: 120 },
      { duration: '30s', target: 0 },
    ],
    paired_fault: 'network_latency on payments-api',
    last_result: { rps: 840, p50_ms: 85, p99_ms: 420, errors_pct: 0.1 },
  },
  {
    id: 'payments-stress',
    name: 'Payments breaking point',
    type: 'stress',
    target: 'payments-api',
    vus: 200,
    duration: '12m',
    ramp: '2m',
    goal: 'Find VU count where p99 exceeds 2s or errors > 1%',
    stages: [
      { duration: '2m', target: 40 },
      { duration: '2m', target: 80 },
      { duration: '2m', target: 120 },
      { duration: '2m', target: 160 },
      { duration: '2m', target: 200 },
      { duration: '2m', target: 0 },
    ],
    paired_fault: 'dependency_blackhole on payments-db',
    last_result: { rps: 520, p50_ms: 310, p99_ms: 1840, errors_pct: 4.6, breaking_point_vus: 140 },
  },
  {
    id: 'checkout-perf',
    name: 'Checkout latency baseline',
    type: 'performance',
    target: 'checkout',
    vus: 20,
    duration: '3m',
    ramp: '10s',
    goal: 'p50 < 80ms, p99 < 250ms at 20 VUs',
    stages: [
      { duration: '10s', target: 20 },
      { duration: '3m', target: 20 },
      { duration: '10s', target: 0 },
    ],
    last_result: { rps: 180, p50_ms: 62, p99_ms: 198, errors_pct: 0 },
  },
  {
    id: 'inventory-soak',
    name: 'Inventory overnight soak',
    type: 'soak',
    target: 'inventory-api',
    vus: 60,
    duration: '2h',
    ramp: '5m',
    goal: 'Stable memory, no connection growth, SQS age < 30s over 2h',
    stages: [
      { duration: '5m', target: 60 },
      { duration: '2h', target: 60 },
      { duration: '5m', target: 0 },
    ],
    paired_fault: 'pod_kill every 15m',
  },
  {
    id: 'inventory-spike',
    name: 'Inventory flash sale',
    type: 'stress',
    target: 'inventory-api',
    vus: 200,
    duration: '8m',
    ramp: '1m',
    goal: 'Spike to 200 VUs in 1m — measure recovery after spike',
    stages: [
      { duration: '1m', target: 200 },
      { duration: '5m', target: 200 },
      { duration: '2m', target: 0 },
    ],
  },
]

export const chaosLoadPairings: ChaosLoadPairing[] = [
  {
    id: 'db-blackhole-load',
    name: 'DB blackhole under peak load',
    load_type: 'load',
    fault: 'toxiproxy dependency_blackhole → payments-db',
    hypothesis: 'Checkout SLO breaches when DB unreachable at peak traffic',
    recommended_vus: 120,
  },
  {
    id: 'latency-stress',
    name: 'Upstream latency + stress ramp',
    load_type: 'stress',
    fault: 'chaos_mesh network_latency 500ms → payments-api',
    hypothesis: 'Breaking point drops when upstream is slow',
    recommended_vus: 80,
  },
  {
    id: 'perf-baseline-fault',
    name: 'Performance regression with fault',
    load_type: 'performance',
    fault: 'toxiproxy timeout → stripe-api',
    hypothesis: 'p99 doubles with 3rd-party timeout under light load',
    recommended_vus: 20,
  },
  {
    id: 'soak-pod-kill',
    name: 'Soak + intermittent pod kill',
    load_type: 'soak',
    fault: 'chaos_mesh pod_kill every 15m',
    hypothesis: 'Connection pools recover over long runs without leak',
    recommended_vus: 60,
  },
]

export const k6ScriptTemplates: Record<LoadTestType, string> = {
  load: `// Load test — sustain expected peak
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 120 },
    { duration: '5m', target: 120 },
    { duration: '30s', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.005'],
    http_req_duration: ['p(99)<500'],
  },
};

export default function () {
  const res = http.get(__ENV.TARGET_URL + '/checkout');
  check(res, { 'status 200': (r) => r.status === 200 });
  sleep(0.3);
}`,
  stress: `// Stress test — ramp until failure
export const options = {
  stages: [
    { duration: '2m', target: 40 },
    { duration: '2m', target: 80 },
    { duration: '2m', target: 120 },
    { duration: '2m', target: 160 },
    { duration: '2m', target: 200 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(99)<2000'], // abort stage when breached
  },
};`,
  performance: `// Performance test — latency-focused, low VUs
export const options = {
  vus: 20,
  duration: '3m',
  thresholds: {
    http_req_duration: ['p(50)<80', 'p(99)<250'],
  },
};`,
  soak: `// Soak test — moderate load, long duration
export const options = {
  stages: [
    { duration: '5m', target: 60 },
    { duration: '2h', target: 60 },
    { duration: '5m', target: 0 },
  ],
  thresholds: {
    http_req_failed: ['rate<0.01'],
  },
};`,
}

export const demoObservabilityLinks = [
  { label: 'Experiment dashboard', url: 'grafana/d/chaos-exp/checkout-payments', type: 'grafana' },
  { label: 'Fault window traces', url: 'tempo/search?tag=experiment%3Dcheckout-001', type: 'tempo' },
  { label: 'SLO breach alert', url: 'prometheus/alerts?filter=checkout_error_rate', type: 'prometheus' },
  { label: 'Correlated incident', url: 'pagerduty/incidents/PXYZ123', type: 'pagerduty' },
]

export const demoBootstrapActions = [
  { action: 'Install Istio', scope: 'k8s', status: 'available', detail: 'Bootstrap service mesh for circuit breakers' },
  { action: 'Create PriorityClass', scope: 'k8s', status: 'available', detail: 'chaos-critical for payments-api' },
  { action: 'Enable RDS Multi-AZ', scope: 'aws', status: 'requires_approval', detail: 'Terraform PR draft ready' },
  { action: 'Add SQS DLQ', scope: 'aws', status: 'available', detail: 'order-events queue policy' },
  { action: 'Provision chaos dashboards', scope: 'observability', status: 'done', detail: 'Grafana folder chaos-agent/' },
]

export const productFeatures: ProductFeature[] = [
  { id: 'orchestrator', name: 'Experiment orchestrator', description: 'Safe lifecycle with rollback and audit', phase: 1, status: 'live', path: '/experiments', icon: 'flask' },
  { id: 'compose', name: 'Human + LLM compose', description: 'Natural language → grounded ExperimentPlan', phase: 2, status: 'live', path: '/new', icon: 'zap' },
  { id: 'infra', name: 'Infrastructure snapshot', description: 'K8s + AWS + app + deps + observability graph', phase: 2, status: 'preview', path: '/infrastructure', icon: 'network' },
  { id: 'twin', name: 'Digital twin', description: 'Blast radius simulation before inject', phase: 2, status: 'preview', path: '/infrastructure', icon: 'layers' },
  { id: 'remediation', name: 'LLM remediation', description: 'Findings → tickets, PRs, runbooks', phase: 2, status: 'preview', path: '/remediation', icon: 'wrench' },
  { id: 'posture', name: 'Posture scanner', description: '5-ring gap detection + bootstrap fixes', phase: 2, status: 'live', path: '/posture', icon: 'shield' },
      { id: 'redblue', name: 'Red vs Blue', description: 'Adversarial agents — optional security attacks + Blue defense', phase: 3, status: 'live', path: '/red-blue', icon: 'swords' },
  { id: 'cigate', name: 'CI resilience gate', description: 'PR-scoped faults + regression comment', phase: 3, status: 'preview', path: '/ci-gate', icon: 'git' },
  { id: 'awsfis', name: 'AWS FIS executor', description: 'AZ impairment, RDS failover experiments', phase: 3, status: 'planned', path: '/policies', icon: 'cloud' },
  { id: 'chaosdna', name: 'Chaos DNA', description: 'Per-service resilience profiles over time', phase: 4, status: 'preview', path: '/chaos-dna', icon: 'dna' },
  { id: 'policies', name: 'Safety policies', description: 'Blast caps, freeze windows, approvals', phase: 1, status: 'preview', path: '/policies', icon: 'lock' },
  { id: 'referee', name: 'Referee', description: 'Scoring rules, freeze calendar, round orchestration', phase: 3, status: 'preview', path: '/referee', icon: 'scale' },
  { id: 'integrations', name: 'Integrations', description: 'Slack, GitHub, PagerDuty, Grafana, Tempo', phase: 2, status: 'preview', path: '/integrations', icon: 'plug' },
  { id: 'observability', name: 'Observability', description: 'Steady-state guard, live metrics, traces', phase: 1, status: 'preview', path: '/observability', icon: 'activity' },
  { id: 'load', name: 'Performance testing', description: 'Load, stress, performance, soak — paired with faults', phase: 2, status: 'preview', path: '/load-testing', icon: 'gauge' },
]

export const roadmapPhases: RoadmapPhase[] = [
  {
    phase: 1,
    title: 'Safe orchestrator',
    status: 'live',
    summary: 'Chaos Mesh + Toxiproxy executors, Prometheus guard, SQLite audit, API + UI shell.',
    features: [
      { name: 'Experiment state machine', status: 'live', path: '/experiments' },
      { name: 'Auto-rollback + TTL safety net', status: 'live', path: '/policies' },
      { name: 'Steady-state guard', status: 'preview', path: '/observability' },
      { name: 'Safety validator', status: 'preview', path: '/referee' },
    ],
  },
  {
    phase: 2,
    title: 'Intelligence layer',
    status: 'preview',
    summary: 'LLM compose + remediation, real collectors, posture bootstrap, Slack approvals.',
    features: [
      { name: 'LLM scenario composer + pre-mortem', status: 'live', path: '/new' },
      { name: 'Infrastructure snapshot (5 rings)', status: 'preview', path: '/infrastructure' },
      { name: 'Digital twin blast simulation', status: 'preview', path: '/infrastructure' },
      { name: 'LLM remediation pipeline', status: 'preview', path: '/remediation' },
      { name: 'Posture bootstrap (Istio, PriorityClass)', status: 'preview', path: '/posture' },
      { name: 'Performance tests (load/stress/soak)', status: 'preview', path: '/load-testing' },
      { name: 'Slack + GitHub integrations', status: 'preview', path: '/integrations' },
    ],
  },
  {
    phase: 3,
    title: 'Adversarial + CI',
    status: 'preview',
    summary: 'Red agent attacks, PR-scoped CI gate, AWS FIS executor, regression suites.',
    features: [
      { name: 'Red agent (break maximizer)', status: 'preview', path: '/red-blue' },
      { name: 'CI resilience gate on PRs', status: 'preview', path: '/ci-gate' },
      { name: 'AWS FIS executor', status: 'planned', path: '/policies' },
      { name: 'Referee scoring + freeze calendar', status: 'preview', path: '/referee' },
      { name: 'Regression suite export', status: 'preview', path: '/ci-gate' },
    ],
  },
  {
    phase: 4,
    title: 'Closed-loop campaigns',
    status: 'planned',
    summary: 'Blue agent defends, equilibrium → regression, Chaos DNA scorecards, staging game-days.',
    features: [
      { name: 'Blue agent (defense maximizer)', status: 'preview', path: '/red-blue' },
      { name: 'Closed-loop Red/Blue in staging', status: 'planned', path: '/red-blue' },
      { name: 'Chaos DNA profiles', status: 'preview', path: '/chaos-dna' },
      { name: 'Resilience score trends', status: 'preview', path: '/chaos-dna' },
    ],
  },
  {
    phase: 'future',
    title: 'Beyond v1',
    status: 'planned',
    summary: 'Multi-cluster, custom executors, GCP/Azure (deferred), digital twin Monte Carlo.',
    features: [
      { name: 'Multi-cluster orchestration', status: 'planned' },
      { name: 'Custom fault plugins', status: 'planned' },
      { name: 'Monte Carlo blast simulation', status: 'planned', path: '/infrastructure' },
      { name: 'Game-day automation', status: 'planned', path: '/red-blue' },
    ],
  },
]

export const demoPolicyYaml = `# Resilience posture policy — K8s + AWS rules the agent enforces.

priority_tiers:
  critical:
    value: 1000000
    match:
      labels:
        tier: critical
  standard:
    value: 100000
    default: true

rules:
  - id: critical-pods-priority-class
    scope: k8s
    severity: high
    when:
      labels:
        tier: critical
    require:
      priority_class: chaos-critical

  - id: critical-rds-multi-az
    scope: aws
    severity: critical
    when:
      tags:
        tier: critical
      service: rds
    require:
      multi_az: true

  - id: app-circuit-breaker
    scope: app
    severity: high
    when:
      labels:
        tier: critical
    require:
      circuit_breaker: true

  - id: deps-third-party-timeout
    scope: deps
    severity: high
    when:
      third_party: true
    require:
      client_timeout_seconds: 5

bootstrap:
  istio:
    mode: prompt_install
    allowed_environments: [development, staging]
  priority_class:
    auto_create_staging: true`

export const demoRefereeScoring = [
  { metric: 'Time to SLO breach', weight: 30, red: 'Faster = higher Red score', blue: 'Slower = higher Blue score' },
  { metric: 'Blast radius contained', weight: 25, red: 'Wider cascade = Red wins', blue: 'Contained = Blue wins' },
  { metric: 'Recovery time', weight: 25, red: 'Slow recovery = Red wins', blue: 'Fast rollback = Blue wins' },
  { metric: 'Remediation landed', weight: 20, red: 'No fix opened = Red wins', blue: 'PR/issue opened = Blue wins' },
]

export const demoFreezeWindows = [
  { label: 'Weekly change freeze', schedule: 'Fri 16:00 → Mon 08:00 UTC', enforced: false, next: 'Fri Jun 20' },
  { label: 'Holiday blackout', schedule: 'Dec 20 → Jan 5', enforced: true, next: 'Dec 20' },
  { label: 'Launch freeze (checkout)', schedule: 'Jun 15–Jun 22', enforced: true, next: 'Active now' },
]

export const demoPolicyRules = [
  { id: 'critical-pods-priority-class', scope: 'k8s', severity: 'high', summary: 'critical tier → chaos-critical PriorityClass' },
  { id: 'critical-deployment-probes', scope: 'k8s', severity: 'high', summary: 'critical tier → readiness + liveness probes' },
  { id: 'critical-rds-multi-az', scope: 'aws', severity: 'critical', summary: 'critical RDS → multi_az=true' },
  { id: 'critical-sqs-dlq', scope: 'aws', severity: 'high', summary: 'critical SQS → dead letter queue' },
  { id: 'app-circuit-breaker', scope: 'app', severity: 'high', summary: 'critical apps → circuit breaker required' },
  { id: 'deps-third-party-timeout', scope: 'deps', severity: 'high', summary: '3rd party deps → 5s client timeout' },
  { id: 'obs-trace-coverage', scope: 'observability', severity: 'high', summary: 'critical paths → traced in Tempo' },
]
