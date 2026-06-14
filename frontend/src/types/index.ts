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
  slo_breached?: boolean
  baseline?: Record<string, number>
  evidence?: FaultWindowEvidence
}

export interface MetricWindowSample {
  name: string
  baseline?: number
  during_peak?: number
  after?: number
  delta_ratio?: number
  unit: string
}

export interface LogSummary {
  service: string
  error_count: number
  top_patterns: string[]
  sample_lines: string[]
}

export interface TraceSummary {
  path: string
  trace_count: number
  error_spans: number
  p99_ms?: number
  sample_trace_ids: string[]
}

export interface FaultWindowEvidence {
  experiment_id: string
  window_start: string
  window_end: string
  simulated: boolean
  metrics: MetricWindowSample[]
  logs: LogSummary[]
  traces: TraceSummary[]
  correlations: string[]
}

export interface ObservabilityBackendStatus {
  prometheus: string
  loki: string
  tempo: string
  detail: Record<string, string | null>
}

export interface DashboardStats {
  experiments_total: number
  experiments_running: number
  avg_resilience_score: number
  posture_gaps: number
  red_blue_campaigns: number
  active_campaign?: RedBlueCampaign | null
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
  live_data?: boolean
  collection_sources?: Record<string, string>
  summary?: {
    k8s: number
    aws: number
    app: number
    deps: number
    observability: number
  }
}

export type PracticeLevel =
  | 'infra'
  | 'db'
  | 'dependency'
  | 'app'
  | 'scaling'
  | 'security'
  | 'monitoring'
  | 'ha'
  | 'resiliency'
  | 'reliability'

export interface ContextGap {
  id: string
  level: PracticeLevel
  scope: PostureGap['scope']
  severity: PostureGap['severity']
  service: string
  rule: string
  message: string
  declared_evidence: string[]
  observed_evidence: string[]
  policy_rule?: string
}

export interface BlueSuggestion {
  finding_id: string
  level: PracticeLevel
  title: string
  action: string
  artifact_type: 'terraform' | 'code' | 'manifest' | 'config' | 'runbook'
  target_path: string
  suggested_diff: string
  requires_approval: boolean
}

export interface ContextSnapshot {
  id: string
  repo_name: string
  namespace: string
  declared: {
    repo_name: string
    terraform_resources: { type: string; name: string; attributes: Record<string, unknown>; source_file: string }[]
    documents: { name: string; doc_type: string; claims: string[]; raw_excerpt: string }[]
    code_hints: string[]
  }
  ingested_at: string
}

export interface ContextAnalysisResult {
  snapshot_id: string
  repo_name: string
  scanned_at: string
  declared_summary: Record<string, number>
  gaps: ContextGap[]
  blue_suggestions: BlueSuggestion[]
  posture_summary: Record<string, number>
  sast_findings?: Record<string, unknown>[]
  sast_simulated?: boolean
}

export interface ContextIngestResponse {
  snapshot: ContextSnapshot
  analysis: ContextAnalysisResult
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
  include_security?: boolean
  security_mix_pct?: number
  attack_plan_id?: string
  planned_attack_count?: number
}

export interface CweEntry {
  id: string
  name: string
  example_cves: string[]
}

export interface FrameworkCategory {
  id: string
  name: string
  description: string
  cwes: CweEntry[]
  mitre_techniques: string[]
}

export interface AttackFramework {
  id: string
  name: string
  version: string
  description: string
  source_url: string
  categories: FrameworkCategory[]
}

export interface GeneratedAttackPlan {
  plan_id?: string
  framework_id: string
  framework_name: string
  namespace: string
  category_ids: string[]
  attacks: SecurityAttackSpec[]
  total_cwes: number
  total_cve_examples: number
  generated_at: string
}

export type AttackCategory = 'resilience' | 'security' | 'hybrid'

export interface SecurityAttackSpec {
  id: string
  name: string
  category: AttackCategory
  technique: string
  target_service: string
  description: string
  cwe?: string
  paired_fault?: string
  severity_if_success: string
  safe_for_staging: boolean
  framework_id?: string
  category_id?: string
  category_name?: string
  cwe_ids?: string[]
  cve_examples?: string[]
  mitre_technique_id?: string
  owasp_rank?: string
}

export interface RedBlueAttack {
  id: string
  category: AttackCategory
  title: string
  service: string
  technique: string
  description: string
  cwe?: string
  paired_fault?: string
  transcript: string
  faults: { type: string; target: string }[]
}

export interface RedBlueDefense {
  attack_id: string
  category: AttackCategory
  title: string
  action: string
  artifact_type: string
  target_path: string
  suggested_diff: string
  transcript: string
}

export interface RedBlueRound {
  round: number
  attack: RedBlueAttack
  defense: RedBlueDefense
  red_points: number
  blue_points: number
  outcome: string
  referee_note: string
  red_transcript: string[]
  blue_transcript: string[]
}

export interface RedBlueCampaignDetail extends RedBlueCampaign {
  rounds: RedBlueRound[]
}

export interface RedBlueRoundResponse {
  campaign: RedBlueCampaign
  round: RedBlueRound
}

export interface ComposeResponse {
  plan: ExperimentPlan
  summary: string
  composer?: 'llm' | 'rules'
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

export type LoadTestType = 'load' | 'stress' | 'performance' | 'soak'

export interface LoadTestStage {
  duration: string
  target: number
}

export interface LoadTestScenario {
  id: string
  name: string
  type: LoadTestType
  target: string
  vus: number
  duration: string
  ramp: string
  goal: string
  stages: LoadTestStage[]
  paired_fault?: string
  last_result?: {
    rps: number
    p50_ms: number
    p99_ms: number
    errors_pct: number
    breaking_point_vus?: number
  }
}

export interface LoadTestTypeInfo {
  type: LoadTestType
  title: string
  question: string
  description: string
  when_to_use: string
  typical_duration: string
  chaos_pairing: string
}

export interface ChaosLoadPairing {
  id: string
  name: string
  load_type: LoadTestType
  fault: string
  hypothesis: string
  recommended_vus: number
}
