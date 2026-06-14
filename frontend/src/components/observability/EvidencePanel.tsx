import { Loader2 } from 'lucide-react'
import type { FaultWindowEvidence } from '@/types'
import { MetricChart } from '@/components/observability/MetricChart'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

type EvidencePanelProps = {
  evidence?: FaultWindowEvidence | null
  sloBreached?: boolean
  loading?: boolean
  error?: string | null
  onCapture?: () => void
  capturing?: boolean
  emptyMessage?: string
}

export function EvidencePanel({
  evidence,
  sloBreached,
  loading,
  error,
  onCapture,
  capturing,
  emptyMessage = 'Evidence is captured automatically when the experiment completes.',
}: EvidencePanelProps) {
  if (loading) {
    return (
      <div className="flex items-center gap-2 text-sm text-muted-foreground">
        <Loader2 className="h-4 w-4 animate-spin" />
        Loading fault-window evidence…
      </div>
    )
  }

  if (!evidence) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-muted-foreground">{error ?? emptyMessage}</p>
        {onCapture && (
          <Button size="sm" variant="outline" disabled={capturing} onClick={onCapture}>
            {capturing ? (
              <>
                <Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />
                Capturing…
              </>
            ) : (
              'Capture evidence'
            )}
          </Button>
        )}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline">
          {new Date(evidence.window_start).toLocaleString()} –{' '}
          {new Date(evidence.window_end).toLocaleString()}
        </Badge>
        {evidence.simulated && <Badge variant="secondary">simulated backends</Badge>}
        {sloBreached && <Badge variant="destructive">SLO breached</Badge>}
      </div>

      {evidence.correlations.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Correlations</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm text-muted-foreground">
            {evidence.correlations.map((line, i) => (
              <p key={i}>• {line}</p>
            ))}
          </CardContent>
        </Card>
      )}

      <MetricChart metrics={evidence.metrics} />

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Logs</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {evidence.logs.map((log) => (
            <div key={log.service} className="rounded-md border border-border p-3 text-xs">
              <p className="font-medium">
                {log.service} — {log.error_count} errors
              </p>
              {log.top_patterns.map((p, i) => (
                <p key={i} className="text-muted-foreground">
                  pattern: {p}
                </p>
              ))}
              {log.sample_lines.slice(0, 2).map((line, i) => (
                <p key={i} className="mt-1 font-mono text-[10px] text-muted-foreground">
                  {line}
                </p>
              ))}
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Traces</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {evidence.traces.map((t) => (
            <div key={t.path} className="rounded-md border border-border p-3 text-xs">
              <p className="font-medium">{t.path}</p>
              <p className="text-muted-foreground">
                {t.trace_count} traces · {t.error_spans} error spans
                {t.p99_ms != null && ` · p99 ${t.p99_ms.toFixed(0)}ms`}
              </p>
              {t.sample_trace_ids.length > 0 && (
                <p className="mt-1 font-mono text-[10px]">{t.sample_trace_ids.join(', ')}</p>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  )
}
