import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  abortExperiment,
  captureExperimentEvidence,
  createExperiment,
  getExperiment,
  getExperimentEvidence,
  listExperiments,
} from '@/api/client'
import { queryKeys } from '@/api/queryKeys'
import type { ExperimentPlan } from '@/types'

const ACTIVE_STATES = new Set(['pending', 'running', 'simulating', 'aborting', 'awaiting_approval'])

export function useExperiments() {
  return useQuery({
    queryKey: queryKeys.experiments,
    queryFn: listExperiments,
    staleTime: 15_000,
  })
}

export function useExperiment(id: string | undefined) {
  return useQuery({
    queryKey: queryKeys.experiment(id ?? ''),
    queryFn: () => getExperiment(id!),
    enabled: Boolean(id),
    staleTime: 5_000,
    refetchInterval: (query) => {
      const state = query.state.data?.state
      // WebSocket handles live updates; poll slowly as fallback only.
      return state && ACTIVE_STATES.has(state) ? 15_000 : false
    },
  })
}

export function useExperimentEvidence(experimentId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: queryKeys.experimentEvidence(experimentId ?? ''),
    queryFn: () => getExperimentEvidence(experimentId!),
    enabled: Boolean(experimentId) && enabled,
    staleTime: 60_000,
    retry: false,
  })
}

export function useCaptureEvidence() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: captureExperimentEvidence,
    onSuccess: (data, experimentId) => {
      queryClient.setQueryData(queryKeys.experimentEvidence(experimentId), data)
      void queryClient.invalidateQueries({ queryKey: queryKeys.experiment(experimentId) })
    },
  })
}

export function useCreateExperiment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (plan: ExperimentPlan) => createExperiment(plan),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.experiments })
      void queryClient.invalidateQueries({ queryKey: queryKeys.dashboard })
    },
  })
}

export function useAbortExperiment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: abortExperiment,
    onSuccess: (_data, experimentId) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.experiment(experimentId) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.experiments })
    },
  })
}
