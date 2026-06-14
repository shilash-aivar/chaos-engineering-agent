import { useQuery } from '@tanstack/react-query'
import { getAgentStatus } from '@/api/client'
import { queryKeys } from '@/api/queryKeys'

export function useAgentStatus() {
  return useQuery({
    queryKey: queryKeys.agentStatus,
    queryFn: getAgentStatus,
    staleTime: 60_000,
  })
}
