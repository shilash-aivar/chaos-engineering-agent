import { useQuery } from '@tanstack/react-query'
import { getContextTargets } from '@/api/client'
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
