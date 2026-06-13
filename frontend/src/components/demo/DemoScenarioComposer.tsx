import { Bot, User } from 'lucide-react'
import { demoScenario } from '@/demo/mockData'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function DemoScenarioComposer() {
  const { userPrompt, plan, preMortem } = demoScenario

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Human + LLM scenario</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex gap-2">
            <User className="mt-1 h-4 w-4 shrink-0 text-muted-foreground" />
            <div className="rounded-lg border border-border bg-muted/50 px-3 py-2 text-sm">
              {userPrompt}
            </div>
          </div>
          <div className="flex gap-2">
            <Bot className="mt-1 h-4 w-4 shrink-0 text-primary" />
            <div className="rounded-lg border border-primary/30 bg-primary/5 px-3 py-2 text-sm text-muted-foreground">
              {preMortem}
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm">Generated experiment plan</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div>
            <p className="font-medium text-sm">{plan.name}</p>
            <p className="text-xs text-muted-foreground">{plan.hypothesis}</p>
          </div>
          <Badge variant="secondary">{plan.blast_radius}</Badge>
          <div>
            <p className="mb-1 text-[10px] font-medium uppercase text-muted-foreground">Faults</p>
            <ul className="space-y-1">
              {plan.faults.map((f, i) => (
                <li key={i} className="rounded border border-border px-2 py-1 text-xs">
                  <span className="text-primary">{f.executor}</span> · {f.type} → {f.target}
                  <span className="text-muted-foreground"> ({f.detail})</span>
                </li>
              ))}
            </ul>
          </div>
          <div>
            <p className="mb-1 text-[10px] font-medium uppercase text-muted-foreground">Infra evidence</p>
            <ul className="space-y-0.5 text-xs text-muted-foreground">
              {plan.infra_evidence.map((e, i) => (
                <li key={i}>• {e}</li>
              ))}
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
