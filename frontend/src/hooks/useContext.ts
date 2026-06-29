import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  deleteContextSnapshot,
  getContextAnalysis,
  getContextAnalysisById,
  getContextSnapshot,
  getContextSnapshots,
  getContextTargets,
  getContextUnderstanding,
  getAwsProbe,
  ingestContext,
  pullGitHubContext,
  runContextAgent,
} from '@/api/client'
import { queryKeys } from '@/api/queryKeys'
import type { TargetContext } from '@/store/appStore'
import { contextOptions } from '@/store/appStore'

export function useContextTargets() {
  return useQuery({
    queryKey: queryKeys.contextTargets,
    queryFn: getContextTargets,
    staleTime: 300_000,
    placeholderData: contextOptions as TargetContext[],
  })
}

export function useContextAnalysis(namespace: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.contextAnalysis(namespace),
    queryFn: () => getContextAnalysis(namespace),
    staleTime: 60_000,
    retry: false,
    enabled,
  })
}

export function useContextAnalysisById(snapshotId: string | null) {
  return useQuery({
    queryKey: queryKeys.contextAnalysisById(snapshotId ?? ''),
    queryFn: () => getContextAnalysisById(snapshotId!),
    enabled: Boolean(snapshotId),
    retry: false,
  })
}

export function useContextSnapshot(namespace: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.contextSnapshot(namespace),
    queryFn: () => getContextSnapshot(namespace),
    staleTime: 60_000,
    retry: false,
    enabled,
  })
}

export function useContextSnapshots(namespace: string) {
  return useQuery({
    queryKey: queryKeys.contextSnapshots(namespace),
    queryFn: () => getContextSnapshots(namespace),
    staleTime: 30_000,
  })
}

export function useContextUnderstanding(namespace: string, snapshotId?: string) {
  return useQuery({
    queryKey: queryKeys.contextUnderstanding(namespace, snapshotId),
    queryFn: () => getContextUnderstanding(namespace, snapshotId),
    staleTime: 60_000,
    retry: false,
  })
}

function invalidateContextQueries(queryClient: ReturnType<typeof useQueryClient>, namespace: string) {
  void queryClient.invalidateQueries({ queryKey: queryKeys.contextSnapshot(namespace) })
  void queryClient.invalidateQueries({ queryKey: queryKeys.contextSnapshots(namespace) })
  void queryClient.invalidateQueries({ queryKey: queryKeys.contextAnalysis(namespace) })
  void queryClient.invalidateQueries({ queryKey: ['context', 'understanding', namespace] })
}

export function useRunContextAgent() {
  return useMutation({
    mutationFn: (body: Parameters<typeof runContextAgent>[0]) => runContextAgent(body),
  })
}

export function useAwsProbe(namespace: string, contextId?: string) {
  return useQuery({
    queryKey: queryKeys.awsProbe(namespace, contextId),
    queryFn: () => getAwsProbe(namespace, contextId),
    staleTime: 60_000,
    retry: false,
  })
}

export function useIngestContext() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: Parameters<typeof ingestContext>[0]) => ingestContext(body),
    onSuccess: (_data, variables) => {
      invalidateContextQueries(queryClient, variables.namespace ?? 'staging')
    },
  })
}

export function usePullGitHubContext() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: Parameters<typeof pullGitHubContext>[0]) => pullGitHubContext(body),
    onSuccess: (_data, variables) => {
      invalidateContextQueries(queryClient, variables.namespace ?? 'staging')
    },
  })
}

export function useDeleteContextSnapshot() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ snapshotId }: { snapshotId: string; namespace: string }) =>
      deleteContextSnapshot(snapshotId),
    onSuccess: (_data, variables) => {
      invalidateContextQueries(queryClient, variables.namespace)
    },
  })
}

export function useRefreshContextAnalysis() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (namespace: string) => getContextAnalysis(namespace, true),
    onSuccess: (_data, namespace) => {
      invalidateContextQueries(queryClient, namespace)
    },
  })
}
