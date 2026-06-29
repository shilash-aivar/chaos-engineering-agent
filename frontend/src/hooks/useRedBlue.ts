import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  generateAttackPlan,
  getCampaign,
  listAttackFrameworks,
  listCampaigns,
  remediateRound,
  runCampaignRound,
  startCampaign,
  verifyRound,
} from '@/api/client'
import { queryKeys } from '@/api/queryKeys'

export function useCampaigns() {
  return useQuery({
    queryKey: queryKeys.campaigns,
    queryFn: listCampaigns,
    refetchInterval: 30_000,
    staleTime: 30_000,
  })
}

export function useCampaign(id: string | null) {
  return useQuery({
    queryKey: queryKeys.campaign(id ?? ''),
    queryFn: () => getCampaign(id!),
    enabled: Boolean(id),
  })
}

export function useAttackFrameworks() {
  return useQuery({
    queryKey: queryKeys.attackFrameworks,
    queryFn: listAttackFrameworks,
    staleTime: 120_000,
  })
}

export function useGenerateAttackPlan() {
  return useMutation({ mutationFn: generateAttackPlan })
}

export function useStartCampaign() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({
      name,
      options,
    }: {
      name: string
      options?: Parameters<typeof startCampaign>[1]
    }) => startCampaign(name, options),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.campaigns })
      void qc.invalidateQueries({ queryKey: ['dashboard'] })
    },
  })
}

export function useRunCampaignRound() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (campaignId: string) => runCampaignRound(campaignId),
    onSuccess: (_data, campaignId) => {
      void qc.invalidateQueries({ queryKey: queryKeys.campaigns })
      void qc.invalidateQueries({ queryKey: queryKeys.campaign(campaignId) })
    },
  })
}

export function useRemediateRound() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ campaignId, round }: { campaignId: string; round: number }) =>
      remediateRound(campaignId, round),
    onSuccess: (_data, { campaignId }) => {
      void qc.invalidateQueries({ queryKey: queryKeys.campaign(campaignId) })
    },
  })
}

export function useVerifyRound() {
  return useMutation({
    mutationFn: ({ campaignId, round }: { campaignId: string; round: number }) =>
      verifyRound(campaignId, round),
  })
}
