import { demoRedBlue } from '@/demo/mockData'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function DemoRedBlueArena() {
  const { campaign, round, maxRounds, redScore, blueScore, rounds } = demoRedBlue

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between pb-2">
        <div>
          <CardTitle className="text-sm">{campaign}</CardTitle>
          <p className="text-xs text-muted-foreground">Adversarial resilience · staging only</p>
        </div>
        <Badge variant="warning">
          Round {round}/{maxRounds}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-lg border border-red-team/40 bg-red-team/10 p-4 text-center">
            <p className="text-xs font-medium text-red-team">Red — Break</p>
            <p className="text-4xl font-bold text-red-team">{redScore}</p>
            <p className="mt-1 text-[10px] text-muted-foreground">maximizes SLO breach</p>
          </div>
          <div className="rounded-lg border border-blue-team/40 bg-blue-team/10 p-4 text-center">
            <p className="text-xs font-medium text-blue-team">Blue — Defend</p>
            <p className="text-4xl font-bold text-blue-team">{blueScore}</p>
            <p className="mt-1 text-[10px] text-muted-foreground">maximizes survival</p>
          </div>
        </div>

        <div className="space-y-2">
          {rounds.map((r) => (
            <div
              key={r.round}
              className={`rounded-md border p-3 text-xs ${
                r.red == null ? 'border-dashed border-border opacity-60' : 'border-border'
              }`}
            >
              <div className="mb-1 flex justify-between font-medium">
                <span>Round {r.round}</span>
                {r.red != null && (
                  <span>
                    <span className="text-red-team">R {r.red}</span>
                    {' · '}
                    <span className="text-blue-team">B {r.blue}</span>
                  </span>
                )}
              </div>
              <p className="text-red-team/90">Attack: {r.attack}</p>
              <p className="text-blue-team/90">Defense: {r.defense}</p>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
