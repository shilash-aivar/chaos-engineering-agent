import { create } from 'zustand'
import type { DashboardStats, ExperimentSummary, PostureGap, RedBlueCampaign } from '@/types'

interface AppState {
  apiHealthy: boolean
  stats: DashboardStats | null
  experiments: ExperimentSummary[]
  postureGaps: PostureGap[]
  campaigns: RedBlueCampaign[]
  context: { cluster: string; namespace: string; environment: string }
  setApiHealthy: (v: boolean) => void
  setStats: (s: DashboardStats) => void
  setExperiments: (e: ExperimentSummary[]) => void
  setPostureGaps: (g: PostureGap[]) => void
  setCampaigns: (c: RedBlueCampaign[]) => void
}

export const useAppStore = create<AppState>((set) => ({
  apiHealthy: false,
  stats: null,
  experiments: [],
  postureGaps: [],
  campaigns: [],
  context: {
    cluster: 'eks-staging',
    namespace: 'staging',
    environment: 'staging',
  },
  setApiHealthy: (apiHealthy) => set({ apiHealthy }),
  setStats: (stats) => set({ stats }),
  setExperiments: (experiments) => set({ experiments }),
  setPostureGaps: (postureGaps) => set({ postureGaps }),
  setCampaigns: (campaigns) => set({ campaigns }),
}))
