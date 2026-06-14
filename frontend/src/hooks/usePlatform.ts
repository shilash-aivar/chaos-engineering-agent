import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  getChaosDna,
  getFreezeCalendar,
  getInfrastructure,
  getIntegrations,
  getLoadTests,
  getPluginsEbpfStatus,
  getPluginsWasm,
  getPolicyPostureRules,
  getPolicyRuntime,
  getPolicyYaml,
  getRefereeScoring,
  getRegressionSuites,
  getTwinAnalysis,
  savePolicyYaml,
  testIntegration,
} from '@/api/client'
import { queryKeys } from '@/api/queryKeys'
import { useAppStore } from '@/store/appStore'

export function useInfrastructure() {
  const namespace = useAppStore((s) => s.context.namespace)
  return useQuery({
    queryKey: queryKeys.infrastructure(namespace),
    queryFn: () => getInfrastructure(namespace),
  })
}

export function useTwinAnalysis(faultTarget = 'payments-api', enabled = true) {
  const namespace = useAppStore((s) => s.context.namespace)
  return useQuery({
    queryKey: queryKeys.twin(namespace, faultTarget),
    queryFn: () => getTwinAnalysis(namespace, faultTarget),
    staleTime: 120_000,
    enabled,
  })
}

export function usePolicyRuntime() {
  return useQuery({ queryKey: queryKeys.policyRuntime, queryFn: getPolicyRuntime })
}

export function usePolicyPostureRules() {
  return useQuery({ queryKey: queryKeys.policyRules, queryFn: getPolicyPostureRules })
}

export function usePolicyYaml() {
  return useQuery({ queryKey: queryKeys.policyYaml, queryFn: getPolicyYaml })
}

export function useIntegrations() {
  return useQuery({
    queryKey: queryKeys.integrations,
    queryFn: getIntegrations,
    refetchInterval: 30_000,
  })
}

export function useChaosDna() {
  const namespace = useAppStore((s) => s.context.namespace)
  return useQuery({
    queryKey: queryKeys.chaosDna(namespace),
    queryFn: () => getChaosDna(namespace),
  })
}

export function useLoadTests() {
  return useQuery({ queryKey: queryKeys.loadTests, queryFn: getLoadTests, staleTime: 120_000 })
}

export function useRefereeScoring() {
  return useQuery({ queryKey: queryKeys.refereeScoring, queryFn: getRefereeScoring })
}

export function useFreezeCalendar() {
  return useQuery({ queryKey: queryKeys.refereeFreeze, queryFn: getFreezeCalendar })
}

export function useRegressionSuites() {
  return useQuery({ queryKey: queryKeys.regression, queryFn: getRegressionSuites })
}

export function usePluginsWasm() {
  return useQuery({ queryKey: ['plugins', 'wasm'], queryFn: getPluginsWasm })
}

export function usePluginsEbpf() {
  return useQuery({ queryKey: ['plugins', 'ebpf'], queryFn: getPluginsEbpfStatus })
}

export function useTestIntegration() {
  return useMutation({ mutationFn: testIntegration })
}

export function useSavePolicyYaml() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: savePolicyYaml,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.policyYaml })
      queryClient.invalidateQueries({ queryKey: queryKeys.policyRules })
    },
  })
}
