import { demoRemediationPipeline } from '@/demo/mockData'
import { DemoRemediationPanel } from '@/components/demo/DemoRemediationPanel'
import { PreviewBanner, PhaseBadge } from '@/components/shared/PreviewBanner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

const statusVariant = {
  open: 'warning',
  in_progress: 'default',
  verified: 'success',
  closed: 'secondary',
} as const

export function RemediationPage() {
  return (
    <div className="space-y-6">
      <PreviewBanner phase={2} />

      <div className="grid gap-4 lg:grid-cols-3">
        {[
          { label: 'Open findings', value: demoRemediationPipeline.filter((f) => f.status === 'open').length },
          { label: 'In progress', value: demoRemediationPipeline.filter((f) => f.status === 'in_progress').length },
          { label: 'Verified', value: demoRemediationPipeline.filter((f) => f.status === 'verified').length },
        ].map(({ label, value }) => (
          <Card key={label}>
            <CardContent className="p-4">
              <p className="text-xs text-muted-foreground">{label}</p>
              <p className="text-2xl font-bold">{value}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Remediation pipeline</CardTitle>
          <p className="text-xs text-muted-foreground">
            LLM diagnoses → prescription → GitHub issue / Terraform PR → verify with re-run
          </p>
        </CardHeader>
        <CardContent className="space-y-2">
          {demoRemediationPipeline.map((f) => (
            <div
              key={f.id}
              className="flex flex-wrap items-start justify-between gap-3 rounded-md border border-border p-3"
            >
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant={f.severity === 'critical' ? 'destructive' : 'warning'}>{f.severity}</Badge>
                  <span className="text-sm font-medium">{f.title}</span>
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{f.prescription}</p>
                <p className="mt-1 text-[10px] text-muted-foreground">
                  {f.experiment_id} · {f.scope}
                  {f.ticket && ` · issue ${f.ticket}`}
                  {f.pr && ` · PR ${f.pr}`}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={statusVariant[f.status]}>{f.status.replace('_', ' ')}</Badge>
                {f.status !== 'verified' && f.status !== 'closed' && (
                  <Button variant="outline" size="sm" disabled>
                    Re-run verify
                  </Button>
                )}
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <div>
        <p className="mb-3 text-sm font-medium">Latest experiment output</p>
        <DemoRemediationPanel />
      </div>

      <Card>
        <CardContent className="flex flex-wrap items-center justify-between gap-3 p-4">
          <div>
            <p className="text-sm font-medium">Runbook generation</p>
            <p className="text-xs text-muted-foreground">
              Auto-draft runbooks from findings and attach to PagerDuty + Confluence
            </p>
          </div>
          <PhaseBadge status="planned" phase={2} />
        </CardContent>
      </Card>
    </div>
  )
}
