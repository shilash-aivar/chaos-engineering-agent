import { useQuery } from '@tanstack/react-query'
import { getSnapshot, scanPosture } from '@/api/client'
import { queryKeys } from '@/api/queryKeys'
import { useAppStore } from '@/store/appStore'

export function usePostureScan() {
  const namespace = useAppStore((s) => s.context.namespace)
  const posture = useQuery({
    queryKey: queryKeys.posture(namespace),
    queryFn: () => scanPosture(namespace),
  })
  const snapshot = useQuery({
    queryKey: queryKeys.snapshot(namespace),
    queryFn: () => getSnapshot(namespace),
    staleTime: 60_000,
  })

  const refetchAll = async () => {
    await Promise.all([posture.refetch(), snapshot.refetch()])
  }

  return {
    posture,
    snapshot,
    namespace,
    refetchAll,
    isLoading: posture.isLoading || snapshot.isLoading,
    isRefetching: posture.isRefetching || snapshot.isRefetching,
  }
}
