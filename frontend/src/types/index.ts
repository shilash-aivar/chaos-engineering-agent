export type ExperimentState =
  | 'pending'
  | 'simulating'
  | 'awaiting_approval'
  | 'running'
  | 'aborting'
  | 'complete'
  | 'failed'

export type ExperimentSource = 'human' | 'llm' | 'red_agent' | 'ci' | 'hybrid'

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
  scope: 'k8s' | 'aws'
  severity: 'critical' | 'high' | 'medium' | 'low'
  service: string
  rule: string
  message: string
  remediation: string
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
