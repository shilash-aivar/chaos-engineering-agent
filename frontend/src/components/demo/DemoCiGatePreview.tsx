import { demoPrComment } from '@/demo/mockData'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function DemoCiGatePreview() {
  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm">CI/CD chaos gate</CardTitle>
        <p className="text-xs text-muted-foreground">PR comment · GitHub Actions status check</p>
      </CardHeader>
      <CardContent>
        <pre className="overflow-auto rounded-lg border border-border bg-muted/40 p-4 text-xs leading-relaxed text-muted-foreground whitespace-pre-wrap font-mono">
          {demoPrComment}
        </pre>
      </CardContent>
    </Card>
  )
}
