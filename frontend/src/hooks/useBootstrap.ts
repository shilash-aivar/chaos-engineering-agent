import { useQuery } from '@tanstack/react-query'
import { getBootstrapStatus } from '@/api/client'
import { useAppStore } from '@/store/appStore'

export function useBootstrapStatus() {
  const context = useAppStore((s) => s.context)
  return useQuery({
    queryKey: ['bootstrap', context.namespace, context.id],
    queryFn: () => getBootstrapStatus(context.namespace, context.id),
    staleTime: 60_000,
  })
}
