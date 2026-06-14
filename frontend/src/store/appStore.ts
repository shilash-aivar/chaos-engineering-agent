import { create } from 'zustand'
import type { DashboardStats, ExperimentSummary, PostureGap, RedBlueCampaign } from '@/types'

export interface TargetContext {
  id: string
  cluster: string
  namespace: string
  environment: string
  aws_account: string
  aws_region: string
  label: string
}

export const contextOptions: TargetContext[] = [
  {
    id: 'eks-staging',
    cluster: 'eks-staging',
    namespace: 'staging',
    environment: 'staging',
    aws_account: '111122223333',
    aws_region: 'us-east-1',
    label: 'eks-staging / staging',
  },
  {
    id: 'eks-staging-platform',
    cluster: 'eks-staging',
    namespace: 'platform',
    environment: 'staging',
    aws_account: '111122223333',
    aws_region: 'us-east-1',
    label: 'eks-staging / platform',
  },
  {
    id: 'eks-prod',
    cluster: 'eks-prod',
    namespace: 'production',
    environment: 'production',
    aws_account: '111122223333',
    aws_region: 'us-east-1',
    label: 'eks-prod / production',
  },
]

interface AppState {
  apiHealthy: boolean
  stats: DashboardStats | null
  experiments: ExperimentSummary[]
  postureGaps: PostureGap[]
  campaigns: RedBlueCampaign[]
  context: TargetContext
  setApiHealthy: (v: boolean) => void
  setStats: (s: DashboardStats) => void
  setExperiments: (e: ExperimentSummary[]) => void
  setPostureGaps: (g: PostureGap[]) => void
  setCampaigns: (c: RedBlueCampaign[]) => void
  setContext: (c: TargetContext) => void
}

export const useAppStore = create<AppState>((set) => ({
  apiHealthy: false,
  stats: null,
  experiments: [],
  postureGaps: [],
  campaigns: [],
  context: contextOptions[0],
  setApiHealthy: (apiHealthy) => set({ apiHealthy }),
  setStats: (stats) => set({ stats }),
  setExperiments: (experiments) => set({ experiments }),
  setPostureGaps: (postureGaps) => set({ postureGaps }),
  setCampaigns: (campaigns) => set({ campaigns }),
  setContext: (context) => set({ context }),
}))
