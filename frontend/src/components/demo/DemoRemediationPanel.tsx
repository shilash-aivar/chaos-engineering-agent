import { ExternalLink } from 'lucide-react'
import { demoFindings } from '@/demo/mockData'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

const severityVariant = {
  critical: 'destructive',
  high: 'warning',
  medium: 'default',
} as const

export function DemoRemediationPanel() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">LLM remediation</CardTitle>
        <p className="text-xs text-muted-foreground">Auto-generated within 5 min of experiment complete</p>
      </CardHeader>
      <CardContent className="space-y-3">
        {demoFindings.map((f) => (
          <div key={f.id} className="rounded-lg border border-border p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <p className="text-sm font-medium">{f.title}</p>
              <div className="flex gap-1.5">
                <Badge variant={severityVariant[f.severity]}>{f.severity}</Badge>
                <Badge variant="outline">{f.scope}</Badge>
              </div>
            </div>
            <p className="mt-2 text-xs text-primary">{f.prescription}</p>
            <div className="mt-2 flex items-center justify-between">
              <Button variant="ghost" size="sm" className="h-7 gap-1 text-xs" disabled>
                <ExternalLink className="h-3 w-3" />
                GitHub {f.ticket}
              </Button>
              <span className="text-[10px] text-muted-foreground">Runbook section auto-filled</span>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
