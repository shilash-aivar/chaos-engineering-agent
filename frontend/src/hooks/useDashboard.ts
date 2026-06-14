import { useQuery } from '@tanstack/react-query'
import { getDashboardStats, listExperiments, scanPosture } from '@/api/client'
import { queryKeys } from '@/api/queryKeys'

import { useAppStore } from '@/store/appStore'

export function useDashboard() {
  const namespace = useAppStore((s) => s.context.namespace)

  const stats = useQuery({
    queryKey: queryKeys.dashboard,
    queryFn: getDashboardStats,
    staleTime: 30_000,
  })

  const experiments = useQuery({
    queryKey: queryKeys.experiments,
    queryFn: listExperiments,
    staleTime: 15_000,
  })

  const posture = useQuery({
    queryKey: queryKeys.posture(namespace),
    queryFn: () => scanPosture(namespace),
    staleTime: 120_000,
    enabled: Boolean(stats.data),
  })

  return {
    stats: stats.data,
    experiments: experiments.data ?? [],
    experimentsLoading: experiments.isLoading,
    postureGaps: posture.data?.gaps ?? [],
    activeCampaign: stats.data?.active_campaign ?? null,
    isLoading: stats.isLoading,
    isExperimentsLoading: experiments.isLoading,
  }
}
