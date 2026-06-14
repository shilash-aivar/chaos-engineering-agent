import { useState } from 'react'
import { CheckCircle2, GitPullRequest, Loader2, ShieldAlert, XCircle } from 'lucide-react'
import { toast } from 'sonner'
import { useCiGateEvaluate } from '@/hooks/useCiGate'
import { useAppStore } from '@/store/appStore'
import { PageHeader, PageShell, StatCard } from '@/components/layout/PageChrome'
import { SecurityDisclaimer } from '@/components/shared/SecurityDisclaimer'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

const SAMPLE_FILES = [
  'src/payments/api/routes.py',
  'infra/rds.tf',
  'k8s/payments-deployment.yaml',
]

export function CiGatePage() {
  const context = useAppStore((s) => s.context)
  const [prNumber, setPrNumber] = useState(1847)
  const evaluateMutation = useCiGateEvaluate()
  const result = evaluateMutation.data

  const run = () => {
    evaluateMutation.mutate(
      {
        pr_number: prNumber,
        changed_files: SAMPLE_FILES,
        changed_services: ['payments-api'],
        namespace: context.namespace,
      },
      {
        onError: () => toast.error('CI gate evaluation failed'),
      },
    )
  }

  return (
    <PageShell>
      <SecurityDisclaimer compact />

      <PageHeader
        title="CI gate"
        description="Evaluate pull requests against OWASP probes and a chaos fault before merge. Posts a GitHub comment with resilience score delta."
        badge={
          <Badge variant="outline" className="font-mono text-[10px]">
            PR #{prNumber}
          </Badge>
        }
      />

      <section className="surface-card mb-6 rounded-lg p-5">
        <h2 className="text-sm font-semibold">Evaluate PR</h2>
        <p className="mt-1 text-xs text-muted-foreground">
          Namespace {context.namespace} · changed files: {SAMPLE_FILES.join(', ')}
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Input
            type="number"
            className="max-w-[140px]"
            value={prNumber}
            onChange={(e) => setPrNumber(Number(e.target.value))}
          />
          <Button onClick={run} disabled={evaluateMutation.isPending}>
            {evaluateMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Evaluating…
              </>
            ) : (
              <>
                <GitPullRequest className="h-4 w-4" />
                Run CI gate check
              </>
            )}
          </Button>
        </div>
      </section>

      {result && (
        <div className="space-y-6">
          <div className="grid gap-4 sm:grid-cols-3">
            <StatCard
              icon={result.passed ? CheckCircle2 : XCircle}
              label="Gate status"
              value={result.passed ? 'Pass' : 'Fail'}
              accent={result.passed ? 'teal' : 'rose'}
            />
            <StatCard
              icon={ShieldAlert}
              label="Probes selected"
              value={result.probes.length}
              accent="amber"
            />
            <StatCard
              icon={GitPullRequest}
              label="Resilience delta"
              value={`${result.resilience_score_before} → ${result.resilience_score_after}`}
              accent="sky"
            />
          </div>

          <section
            className={`rounded-lg border p-5 ${
              result.passed
                ? 'border-success/30 bg-success/5'
                : 'border-destructive/30 bg-destructive/5'
            }`}
          >
            <div className="flex items-center gap-2">
              {result.passed ? (
                <CheckCircle2 className="h-5 w-5 text-success" />
              ) : (
                <XCircle className="h-5 w-5 text-destructive" />
              )}
              <p className="font-semibold">
                {result.passed ? 'Merge allowed' : 'Merge blocked'} — PR #{result.pr_number}
              </p>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              Fault: {result.fault.executor} / {result.fault.type} on {result.fault.target}
            </p>
          </section>

          <section className="surface-card rounded-lg">
            <div className="border-b border-border px-5 py-4">
              <h3 className="text-sm font-semibold">Selected probes</h3>
            </div>
            <div className="divide-y divide-border">
              {result.probes.map((p) => (
                <div key={p.id} className="flex flex-wrap items-center gap-2 px-5 py-3 text-sm">
                  <Badge variant="outline">{p.cwe}</Badge>
                  <span className="font-medium">{p.name}</span>
                  <span className="text-muted-foreground">→ {p.target_service}</span>
                </div>
              ))}
            </div>
          </section>

          <section className="surface-card rounded-lg">
            <div className="border-b border-border px-5 py-4">
              <h3 className="text-sm font-semibold">GitHub comment preview</h3>
            </div>
            <pre className="overflow-auto px-5 py-4 font-mono text-xs leading-relaxed whitespace-pre-wrap">
              {result.comment_markdown}
            </pre>
          </section>
        </div>
      )}
    </PageShell>
  )
}
