import axios from 'axios'
import type {
  ComposeResponse,
  ContextAnalysisResult,
  ContextIngestResponse,
  ContextSnapshot,
  DashboardStats,
  ExperimentDetail,
  ExperimentPlan,
  ExperimentSummary,
  InfraSnapshot,
  PostureScanResult,
  AttackFramework,
  GeneratedAttackPlan,
  RedBlueCampaign,
  RedBlueCampaignDetail,
  RedBlueRoundResponse,
  SecurityAttackSpec,
  FaultWindowEvidence,
  ObservabilityBackendStatus,
  IntegrationConfig,
  ChaosDnaProfile,
} from '@/types'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

export async function getHealth() {
  const { data } = await api.get<{
    status: string
    version: string
    environment: string
    components: Record<string, string>
    auth_required: boolean
  }>('/health')
  return data
}

export async function getDashboardStats() {
  const { data } = await api.get<DashboardStats>('/dashboard/stats')
  return data
}

export async function listExperiments() {
  const { data } = await api.get<ExperimentSummary[]>('/experiments')
  return data
}

export async function getExperiment(id: string) {
  const { data } = await api.get<ExperimentDetail>(`/experiments/${id}`)
  return data
}

export async function createExperiment(plan: ExperimentPlan) {
  const { data } = await api.post<ExperimentSummary>('/experiments', plan)
  return data
}

export async function composeScenario(scenario: string, namespace = 'staging') {
  const { data } = await api.post<ComposeResponse>('/experiments/compose', {
    scenario,
    namespace,
  })
  return data
}

export async function composeFullScenario(scenario: string, namespace = 'staging') {
  const { data } = await api.post<{
    plan: ExperimentPlan
    summary: string
    composer: 'llm' | 'rules'
    pre_mortem: Record<string, unknown>
    referee: { passed: boolean; errors: string[] }
    twin_preview?: Record<string, unknown>
  }>('/experiments/compose-full', { scenario, namespace })
  return data
}

export async function approveExperiment(id: string) {
  const { data } = await api.post<{ status: string; experiment_id: string }>(
    `/experiments/${id}/approve`,
  )
  return data
}

export async function planRedAttack(body: {
  round_num?: number
  namespace?: string
  include_security?: boolean
  security_mix_pct?: number
  prior_techniques?: string[]
}) {
  const { data } = await api.post<Record<string, unknown>>('/agents/red/plan', body)
  return data
}

export async function defendRedAttack(body: {
  attack: Record<string, unknown>
  namespace?: string
  evidence_summary?: string[]
}) {
  const { data } = await api.post<Record<string, unknown>>('/agents/blue/defend', body)
  return data
}

export async function verifyRemediationFinding(experimentId: string, findingId: string) {
  const { data } = await api.post<Record<string, unknown>>(
    `/remediation/experiments/${experimentId}/findings/${findingId}/verify`,
  )
  return data
}

export async function getFindingRunbook(experimentId: string, findingId: string) {
  const { data } = await api.get<{ markdown: string }>(
    `/remediation/experiments/${experimentId}/findings/${findingId}/runbook`,
  )
  return data
}

export async function validateRefereePlan(plan: ExperimentPlan) {
  const { data } = await api.post<{ passed: boolean; errors: string[] }>(
    '/agents/referee/validate',
    { plan },
  )
  return data
}

export async function abortExperiment(id: string) {
  const { data } = await api.post<{ status: string }>(`/experiments/${id}/abort`)
  return data
}

export async function scanPosture(namespace = 'staging') {
  const { data } = await api.get<PostureScanResult>('/posture/scan', { params: { namespace } })
  return data
}

export async function getSnapshot(namespace = 'staging') {
  const { data } = await api.get<InfraSnapshot>('/snapshot', { params: { namespace } })
  return data
}

export async function listCampaigns() {
  const { data } = await api.get<RedBlueCampaign[]>('/red-blue/campaigns')
  return data
}

export async function startCampaign(
  name: string,
  options?: {
    namespace?: string
    include_security?: boolean
    security_mix_pct?: number
    attack_framework_id?: string
    attack_category_ids?: string[]
    attack_plan_id?: string
  },
) {
  const { data } = await api.post<RedBlueCampaign>('/red-blue/campaigns', {
    name,
    namespace: options?.namespace ?? 'staging',
    include_security: options?.include_security ?? false,
    security_mix_pct: options?.security_mix_pct ?? 50,
    attack_framework_id: options?.attack_framework_id,
    attack_category_ids: options?.attack_category_ids ?? [],
    attack_plan_id: options?.attack_plan_id,
  })
  return data
}

export async function getCampaign(id: string) {
  const { data } = await api.get<RedBlueCampaignDetail>(`/red-blue/campaigns/${id}`)
  return data
}

export async function runCampaignRound(id: string) {
  const { data } = await api.post<RedBlueRoundResponse>(`/red-blue/campaigns/${id}/round`)
  return data
}

export async function listSecurityAttacks() {
  const { data } = await api.get<SecurityAttackSpec[]>('/red-blue/security/attacks')
  return data
}

export async function listAttackFrameworks() {
  const { data } = await api.get<AttackFramework[]>('/red-blue/security/frameworks')
  return data
}

export async function getAttackFramework(id: string) {
  const { data } = await api.get<AttackFramework>(`/red-blue/security/frameworks/${id}`)
  return data
}

export async function generateAttackPlan(body: {
  framework_id: string
  namespace?: string
  category_ids?: string[]
  target_services?: Record<string, string>
}) {
  const { data } = await api.post<GeneratedAttackPlan>('/red-blue/security/generate', {
    framework_id: body.framework_id,
    namespace: body.namespace ?? 'staging',
    category_ids: body.category_ids ?? [],
    target_services: body.target_services ?? {},
  })
  return data
}

export async function getAttackPlan(planId: string) {
  const { data } = await api.get<GeneratedAttackPlan>(`/red-blue/security/plans/${planId}`)
  return data
}

export async function remediateRound(campaignId: string, roundNum: number) {
  const { data } = await api.post<{
    remediation_id: string
    pr_url?: string
    pr_number?: number
    dry_run: boolean
    title?: string
  }>(`/red-blue/campaigns/${campaignId}/rounds/${roundNum}/remediate`)
  return data
}

export async function verifyRound(campaignId: string, roundNum: number) {
  const { data } = await api.post<{
    verified: boolean
    probe: string
    message: string
    simulated: boolean
    defense: string
  }>(`/red-blue/campaigns/${campaignId}/rounds/${roundNum}/verify`)
  return data
}

export async function evaluateCiGate(body: {
  pr_number: number
  changed_files?: string[]
  changed_services?: string[]
  namespace?: string
}) {
  const { data } = await api.post<{
    pr_number: number
    passed: boolean
    probes: SecurityAttackSpec[]
    fault: { executor: string; type: string; target: string }
    comment_markdown: string
    resilience_score_before: number
    resilience_score_after: number
  }>('/ci-gate/evaluate', body)
  return data
}

export async function ingestContext(body: {
  repo_name: string
  namespace?: string
  terraform_files?: Record<string, string>
  readme_content?: string
  documents?: { name: string; content: string; type?: string }[]
  code_files?: Record<string, string>
}) {
  const { data } = await api.post<ContextIngestResponse>('/context/ingest', body)
  return data
}

export async function getContextSnapshot(namespace = 'staging') {
  const { data } = await api.get<ContextSnapshot>('/context/snapshot', { params: { namespace } })
  return data
}

export async function getContextAnalysis(namespace = 'staging', refresh = false) {
  const { data } = await api.get<ContextAnalysisResult>('/context/analysis', {
    params: { namespace, refresh },
  })
  return data
}

export async function getObservabilityStatus() {
  const { data } = await api.get<ObservabilityBackendStatus>('/observability/status')
  return data
}

export async function getObservabilityCatalog() {
  const { data } = await api.get<{
    services: Record<string, { metrics: string[]; log_selector: string }>
    paths: Record<string, { services: string[]; trace_query: string }>
  }>('/observability/catalog')
  return data
}

export async function getExperimentEvidence(experimentId: string) {
  const { data } = await api.get<FaultWindowEvidence>(`/observability/evidence/${experimentId}`)
  return data
}

export async function captureExperimentEvidence(experimentId: string) {
  const { data } = await api.post<FaultWindowEvidence>(
    `/observability/evidence/${experimentId}/capture`,
  )
  return data
}

export async function getRemediationFindings() {
  const { data } = await api.get<import('@/types').RemediationFinding[]>('/remediation/findings')
  return data
}

export async function runRemediation(experimentId: string) {
  const { data } = await api.post<{
    experiment_id: string
    findings_count: number
    mode: string
    summary: string
    tickets_created: number
  }>(`/remediation/experiments/${experimentId}/run`)
  return data
}

export async function getAgentStatus() {
  const { data } = await api.get<{
    llm_enabled: boolean
    llm_available: boolean
    model: string | null
    agents: Record<string, string>
  }>('/agents/status')
  return data
}

export async function getExperimentRemediation(experimentId: string) {
  const { data } = await api.get<{
    experiment_id: string
    findings: Array<{
      id: string
      severity: string
      title: string
      prescription: string
      scope: string
      status: string
      evidence?: string[]
    }>
    summary: string
    mode: string
  }>(`/remediation/experiments/${experimentId}`)
  return data
}

export async function getInfrastructure(namespace = 'staging') {
  const { data } = await api.get<{
    rings: Record<string, Array<{ name: string; detail: string; status: string }>>
    snapshot: InfraSnapshot
    namespace: string
  }>('/platform/infrastructure', { params: { namespace } })
  return data
}

export async function getTwinAnalysis(namespace = 'staging', faultTarget = 'payments-api') {
  const { data } = await api.get<{
    paths_analyzed: number
    failure_probability_pct: number
    predicted_cascade: string
    blast_path: string[]
    topology: { nodes: Array<{ id: string; label: string; x: number; y: number; tier: string }>; edges: Array<{ from: string; to: string }>; blast_path: string[] }
  }>('/platform/twin', { params: { namespace, fault_target: faultTarget } })
  return data
}

export async function getPolicyRuntime() {
  const { data } = await api.get<{
    policies: Array<{ id: string; name: string; value: string; enforced: boolean; description: string }>
    executors: Array<{ name: string; status: string; detail: string }>
  }>('/policies/runtime')
  return data
}

export async function getPolicyPostureRules() {
  const { data } = await api.get<{
    rules: Array<{ id: string; scope: string; severity: string; summary: string }>
  }>('/policies/posture-rules')
  return data
}

export async function getPolicyYaml() {
  const { data } = await api.get<{ yaml: string; editable: boolean }>('/policies/yaml')
  return data
}

export async function savePolicyYaml(yaml: string) {
  const { data } = await api.put<{ saved: boolean; path: string; rules_count: number }>(
    '/policies/yaml',
    { yaml },
  )
  return data
}

export async function getPluginsWasm() {
  const { data } = await api.get<{
    enabled: boolean
    runtime: string
    plugins: Array<{ id: string; name: string; runtime: string; builtin: boolean; description?: string }>
  }>('/plugins/wasm')
  return data
}

export async function getPluginsEbpfStatus() {
  const { data } = await api.get<{
    enabled: boolean
    use_tc: boolean
    simulate: boolean
    active_programs: Array<Record<string, unknown>>
    active_count: number
  }>('/plugins/ebpf/status')
  return data
}

export async function testIntegration(integrationId: string) {
  const { data } = await api.post<{ ok: boolean; message: string; latency_ms: number }>(
    `/integrations/${integrationId}/test`,
  )
  return data
}

export async function runLoadScenario(
  scenarioId: string,
  options?: { namespace?: string; include_fault?: boolean; start?: boolean },
) {
  const { data } = await api.post<{
    experiment_id: string
    scenario_id: string
    started: boolean
    summary: ExperimentSummary
  }>(`/load-tests/scenarios/${scenarioId}/run`, {
    namespace: options?.namespace ?? 'staging',
    include_fault: options?.include_fault ?? true,
    start: options?.start ?? true,
  })
  return data
}

export async function getIntegrations() {
  const { data } = await api.get<{ integrations: IntegrationConfig[] }>('/integrations')
  return data.integrations
}

export async function getChaosDna(namespace = 'staging') {
  const { data } = await api.get<{
    org_score: number
    org_delta: string
    faults_survived_avg: number
    mttr_seconds: number
    regression_suites_passing: number
    profiles: ChaosDnaProfile[]
    history: Array<{ week: string; score: number }>
  }>('/chaos-dna', { params: { namespace } })
  return data
}

export async function getLoadTests() {
  const { data } = await api.get<{
    types: Array<Record<string, string>>
    scenarios: Array<Record<string, unknown>>
    pairings: Array<Record<string, unknown>>
    templates: Record<string, string>
  }>('/load-tests')
  return data
}

export async function getRefereeScoring() {
  const { data } = await api.get<{
    weights: Array<{ metric: string; weight: number; red: string; blue: string }>
  }>('/platform/scoring')
  return data.weights
}

export async function getFreezeCalendar() {
  const { data } = await api.get<{
    windows: Array<{ label: string; schedule: string; next: string; enforced: boolean }>
    active_reason: string | null
    blocked: boolean
  }>('/platform/freeze')
  return data
}

export async function getRegressionSuites() {
  const { data } = await api.get<{
    suites: Array<{ id: string; name: string; source: string; tests: number; passing: number; last_run: string }>
  }>('/platform/regression')
  return data.suites
}
