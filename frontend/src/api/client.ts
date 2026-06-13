import axios from 'axios'
import type {
  ComposeResponse,
  DashboardStats,
  ExperimentDetail,
  ExperimentPlan,
  ExperimentSummary,
  PostureGap,
  RedBlueCampaign,
} from '@/types'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

export async function getHealth() {
  const { data } = await api.get<{ status: string }>('/health')
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

export async function abortExperiment(id: string) {
  const { data } = await api.post<{ status: string }>(`/experiments/${id}/abort`)
  return data
}

export async function scanPosture() {
  const { data } = await api.get<{ gaps: PostureGap[]; scanned_at: string }>('/posture/scan')
  return data
}

export async function listCampaigns() {
  const { data } = await api.get<RedBlueCampaign[]>('/red-blue/campaigns')
  return data
}

export async function startCampaign(name: string) {
  const { data } = await api.post<RedBlueCampaign>('/red-blue/campaigns', { name })
  return data
}
