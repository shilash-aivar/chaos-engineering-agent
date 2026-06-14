import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getContextAnalysis, ingestContext } from '@/api/client'
import { queryKeys } from '@/api/queryKeys'

export function useContextAnalysis(namespace: string) {
  return useQuery({
    queryKey: queryKeys.contextAnalysis(namespace),
    queryFn: () => getContextAnalysis(namespace),
  })
}

export function useRefreshContextAnalysis() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (namespace: string) => getContextAnalysis(namespace, true),
    onSuccess: (data, namespace) => {
      qc.setQueryData(queryKeys.contextAnalysis(namespace), data)
    },
  })
}

export function useIngestContext() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ingestContext,
    onSuccess: (_data, vars) => {
      void qc.invalidateQueries({
        queryKey: queryKeys.contextAnalysis(vars.namespace ?? 'staging'),
      })
    },
  })
}
