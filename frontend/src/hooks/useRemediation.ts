import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  approveExperiment,
  getExperimentRemediation,
  getFindingRunbook,
  getRemediationFindings,
  runRemediation,
  verifyRemediationFinding,
} from '@/api/client'
import { queryKeys } from '@/api/queryKeys'

export function useRemediationFindings() {
  return useQuery({
    queryKey: queryKeys.remediationFindings,
    queryFn: getRemediationFindings,
    staleTime: 30_000,
    refetchInterval: 60_000,
  })
}

export function useExperimentRemediation(experimentId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: queryKeys.experimentRemediation(experimentId ?? ''),
    queryFn: () => getExperimentRemediation(experimentId!),
    enabled: Boolean(experimentId) && enabled,
  })
}

export function useRunRemediation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: runRemediation,
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.remediationFindings })
      void qc.invalidateQueries({ queryKey: ['experiments'] })
    },
  })
}

export function useVerifyFinding() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ experimentId, findingId }: { experimentId: string; findingId: string }) =>
      verifyRemediationFinding(experimentId, findingId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.remediationFindings })
      void qc.invalidateQueries({ queryKey: ['experiments'] })
    },
  })
}

export function useFindingRunbook() {
  return useMutation({
    mutationFn: ({ experimentId, findingId }: { experimentId: string; findingId: string }) =>
      getFindingRunbook(experimentId, findingId),
  })
}

export function useApproveExperiment() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: approveExperiment,
    onSuccess: (_data, experimentId) => {
      void qc.invalidateQueries({ queryKey: queryKeys.experiment(experimentId) })
      void qc.invalidateQueries({ queryKey: ['experiments'] })
    },
  })
}
