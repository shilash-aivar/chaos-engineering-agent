import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { queryKeys } from '@/api/queryKeys'
import { wsAuthQuery } from '@/lib/apiAuth'
import type { ExperimentDetail } from '@/types'

const ACTIVE_STATES = new Set(['pending', 'running', 'simulating', 'aborting', 'awaiting_approval'])

function wsUrl(experimentId: string): string {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}/api/ws/experiments/${experimentId}${wsAuthQuery()}`
}

export function useExperimentWebSocket(experimentId: string | undefined, enabled = true) {
  const queryClient = useQueryClient()
  const socketRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!experimentId || !enabled) return

    const current = queryClient.getQueryData<ExperimentDetail>(queryKeys.experiment(experimentId))
    if (current && !ACTIVE_STATES.has(current.state)) return

    let closed = false
    const socket = new WebSocket(wsUrl(experimentId))
    socketRef.current = socket

    socket.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data as string) as {
          type?: string
          data?: ExperimentDetail
          state?: string
        }
        if (msg.type === 'experiment' && msg.data) {
          queryClient.setQueryData(queryKeys.experiment(experimentId), msg.data)
        }
        if (msg.type === 'done') {
          socket.close()
        }
      } catch {
        // ignore malformed frames
      }
    }

    socket.onclose = () => {
      if (!closed) {
        void queryClient.invalidateQueries({ queryKey: queryKeys.experiment(experimentId) })
      }
    }

    return () => {
      closed = true
      socket.close()
      socketRef.current = null
    }
  }, [experimentId, enabled, queryClient])
}
