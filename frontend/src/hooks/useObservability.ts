import { useQuery } from '@tanstack/react-query'
import { getObservabilityCatalog, getObservabilityStatus } from '@/api/client'
import { queryKeys } from '@/api/queryKeys'

export function useObservabilityStatus() {
  return useQuery({
    queryKey: queryKeys.observabilityStatus,
    queryFn: getObservabilityStatus,
    refetchInterval: 30_000,
  })
}

export function useObservabilityCatalog() {
  return useQuery({
    queryKey: queryKeys.observabilityCatalog,
    queryFn: getObservabilityCatalog,
    staleTime: 60_000,
  })
}
