import { Loader2, Wrench, FileText, CheckCircle2 } from 'lucide-react'
import { toast } from 'sonner'
import { useRemediationFindings, useVerifyFinding, useFindingRunbook } from '@/hooks/useRemediation'
import { PageHeader, PageShell, StatCard, EmptyState } from '@/components/layout/PageChrome'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useQuery } from '@tanstack/react-query'
import { getAgentStatus } from '@/api/client'
import { queryKeys } from '@/api/queryKeys'

const statusVariant = {
  open: 'warning',
  in_progress: 'default',
  verified: 'success',
  closed: 'secondary',
} as const

export function RemediationPage() {
  const { data: findings = [], isLoading } = useRemediationFindings()
  const verifyMutation = useVerifyFinding()
  const runbookMutation = useFindingRunbook()
  const { data: agentStatus } = useQuery({
    queryKey: queryKeys.agentStatus,
    queryFn: getAgentStatus,
    staleTime: 60_000,
  })

  const open = findings.filter((f) => f.status === 'open').length
  const inProgress = findings.filter((f) => f.status === 'in_progress').length
  const verified = findings.filter((f) => f.status === 'verified').length

  const handleVerify = (experimentId: string, findingId: string) => {
    verifyMutation.mutate(
      { experimentId, findingId },
      {
        onSuccess: (data) =>
          toast.success(data.verified ? 'Finding verified' : 'Verification failed — SLO still breaches'),
        onError: () => toast.error('Verify request failed'),
      },
    )
  }

  const handleRunbook = (experimentId: string, findingId: string) => {
    runbookMutation.mutate(
      { experimentId, findingId },
      {
        onSuccess: (data) => {
          const blob = new Blob([data.markdown], { type: 'text/markdown' })
          const url = URL.createObjectURL(blob)
          const a = document.createElement('a')
          a.href = url
          a.download = `runbook-${findingId}.md`
          a.click()
          URL.revokeObjectURL(url)
          toast.success('Runbook downloaded')
        },
        onError: () => toast.error('Could not fetch runbook'),
      },
    )
  }

  if (isLoading) {
    return (
      <PageShell>
        <Skeleton className="h-24 rounded-lg" />
        <Skeleton className="mt-6 h-96 rounded-lg" />
      </PageShell>
    )
  }

  return (
    <PageShell>
      <PageHeader
        title="Remediation"
        description="Post-experiment findings from the Remediator agent — evidence → prescription → GitHub issues → verify."
        badge={
          agentStatus ? (
            <Badge variant="outline" className="font-mono text-[10px]">
              {agentStatus.agents.remediator}
              {agentStatus.llm_available ? ` · ${agentStatus.model}` : ' · rules only'}
            </Badge>
          ) : undefined
        }
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <StatCard icon={Wrench} label="Open findings" value={open} accent="amber" />
        <StatCard icon={Wrench} label="In progress" value={inProgress} accent="sky" />
        <StatCard icon={Wrench} label="Verified" value={verified} accent="teal" />
      </div>

      {findings.length === 0 ? (
        <EmptyState
          icon={Wrench}
          title="No remediation findings yet"
          description="Complete a chaos experiment — the Remediator agent runs automatically after fault-window evidence is captured."
        />
      ) : (
        <section className="surface-card rounded-lg">
          <div className="border-b border-border px-5 py-4">
            <h2 className="text-sm font-semibold">Remediation pipeline</h2>
            <p className="text-xs text-muted-foreground">
              LLM or rule-based diagnosis → prescription → GitHub issue → re-run verify
            </p>
          </div>
          <div className="divide-y divide-border">
            {findings.map((f) => (
              <div key={f.id} className="flex flex-wrap items-start justify-between gap-3 px-5 py-4">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant={f.severity === 'critical' ? 'destructive' : 'warning'}>
                      {f.severity}
                    </Badge>
                    <span className="text-sm font-medium">{f.title}</span>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{f.prescription}</p>
                  <p className="mt-1 font-mono text-[10px] text-muted-foreground">
                    {f.experiment_id} · {f.scope}
                    {f.ticket && ` · issue #${f.ticket}`}
                    {f.pr && ` · PR #${f.pr}`}
                  </p>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={statusVariant[f.status]}>{f.status.replace('_', ' ')}</Badge>
                  {f.status !== 'verified' && f.experiment_id && (
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={verifyMutation.isPending}
                      onClick={() => handleVerify(f.experiment_id!, f.id)}
                    >
                      <CheckCircle2 className="h-3.5 w-3.5" />
                      Verify
                    </Button>
                  )}
                  {f.experiment_id && (
                    <Button
                      size="sm"
                      variant="ghost"
                      disabled={runbookMutation.isPending}
                      onClick={() => handleRunbook(f.experiment_id!, f.id)}
                    >
                      <FileText className="h-3.5 w-3.5" />
                      Runbook
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {isLoading && (
        <div className="mt-4 flex justify-center">
          <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        </div>
      )}
    </PageShell>
  )
}
