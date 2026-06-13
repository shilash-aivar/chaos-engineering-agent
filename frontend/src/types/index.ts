export type ExperimentState =
  | 'pending'
  | 'simulating'
  | 'awaiting_approval'
  | 'running'
  | 'aborting'
  | 'complete'
  | 'failed'

export type ExperimentSource = 'human' | 'llm' | 'red_agent' | 'ci' | 'hybrid'

export type FeaturePhase = 1 | 2 | 3 | 4 | 'future'
export type FeatureStatus = 'live' | 'preview' | 'planned'

export interface ExperimentSummary {
  id: string
  name: string
  hypothesis: string
  state: ExperimentState
  source: ExperimentSource
  namespace: string
  environment: string
  created_at: string
  red_score?: number
  blue_score?: number
}

export interface ExperimentPlan {
  name: string
  hypothesis: string
  source: ExperimentSource
  targets: { service: string; namespace: string }[]
  faults: { executor: string; type: string; target?: string; params?: Record<string, unknown> }[]
  infra_evidence: string[]
  blast_radius: { max_replicas_pct: number; namespace: string; environment: string }
  watch_metrics: string[]
  rollback: { type: string; ttl_seconds: number }
}

export interface ExperimentDetail extends ExperimentSummary {
  plan: ExperimentPlan
  timeline: { at: string; event: string; detail?: string }[]
  findings_count: number
}

export interface DashboardStats {
  experiments_total: number
  experiments_running: number
  avg_resilience_score: number
  posture_gaps: number
  red_blue_campaigns: number
  last_experiment_at?: string
}

export interface PostureGap {
  id: string
  scope: 'k8s' | 'aws' | 'app' | 'deps' | 'observability'
  severity: 'critical' | 'high' | 'medium' | 'low'
  service: string
  rule: string
  message: string
  remediation: string
}

export interface PostureScanResult {
  gaps: PostureGap[]
  scanned_at: string
  summary?: {
    k8s: number
    aws: number
    app: number
    deps: number
    observability: number
  }
}

export interface InfraSnapshot {
  captured_at: string
  context: {
    cluster: string
    namespace: string
    aws_account: string
    aws_region: string
    environment: string
  }
  applications: { name: string; tier: string; has_retry: boolean; has_circuit_breaker: boolean }[]
  dependencies: { name: string; type: string; owner_service: string; third_party: boolean }[]
  observability: { name: string; type: string; status: string; detail?: string }[]
  graph_edges: { from: string; to: string; type: string }[]
}

export interface RedBlueCampaign {
  id: string
  name: string
  state: 'active' | 'complete'
  round: number
  max_rounds: number
  red_score: number
  blue_score: number
  leader: 'red' | 'blue' | 'draw'
  last_round_at: string
}

export interface ComposeResponse {
  plan: ExperimentPlan
  summary: string
}

export interface RoadmapPhase {
  phase: FeaturePhase
  title: string
  status: FeatureStatus
  summary: string
  features: { name: string; status: FeatureStatus; path?: string }[]
}

export interface ProductFeature {
  id: string
  name: string
  description: string
  phase: FeaturePhase
  status: FeatureStatus
  path: string
  icon: string
}

export interface RemediationFinding {
  id: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  title: string
  prescription: string
  ticket?: string
  pr?: string
  scope: string
  status: 'open' | 'in_progress' | 'verified' | 'closed'
  experiment_id?: string
}

export interface ChaosDnaProfile {
  service: string
  tier: string
  resilience_score: number
  faults_survived: string[]
  weak_points: string[]
  last_tested: string
  trend: 'up' | 'down' | 'flat'
}

export interface SafetyPolicy {
  id: string
  name: string
  value: string
  enforced: boolean
  description: string
}

export interface IntegrationConfig {
  id: string
  name: string
  type: 'slack' | 'github' | 'pagerduty' | 'grafana' | 'tempo' | 'prometheus'
  status: 'connected' | 'disconnected' | 'planned'
  detail: string
  events: string[]
}

export interface RegressionSuite {
  id: string
  name: string
  source: 'red_blue' | 'experiment' | 'manual'
  tests: number
  passing: number
  last_run: string
}

export interface LoadTestScenario {
  id: string
  name: string
  target: string
  vus: number
  duration: string
  ramp: string
  last_result?: { rps: number; p99_ms: number; errors_pct: number }
}
