import { useQuery } from '@tanstack/react-query'
import { getHealth } from '@/api/client'
import { queryKeys } from '@/api/queryKeys'

export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: getHealth,
    staleTime: 60_000,
    refetchInterval: 60_000,
    retry: false,
  })
}
