import { useMutation } from '@tanstack/react-query'
import { evaluateCiGate } from '@/api/client'

export function useCiGateEvaluate() {
  return useMutation({ mutationFn: evaluateCiGate })
}
