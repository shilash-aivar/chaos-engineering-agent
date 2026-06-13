import { TrendingDown, TrendingUp, Minus } from 'lucide-react'
import { demoChaosDna } from '@/demo/mockData'
import { DemoResilienceTrend } from '@/components/demo/DemoResilienceTrend'
import { PreviewBanner, PhaseBadge } from '@/components/shared/PreviewBanner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

const trendIcon = {
  up: TrendingUp,
  down: TrendingDown,
  flat: Minus,
}

export function ChaosDnaPage() {
  return (
    <div className="space-y-6">
      <PreviewBanner phase={4} liveHint="Chaos DNA tracks per-service resilience over repeated experiments and Red/Blue rounds." />

      <div className="grid gap-4 lg:grid-cols-2">
        <DemoResilienceTrend />
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Org resilience score</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-4xl font-bold">73</p>
            <p className="text-xs text-muted-foreground">+15 over 6 weeks · staging aggregate</p>
            <div className="mt-4 space-y-2 text-xs">
              <div className="flex justify-between">
                <span>Faults survived (avg)</span>
                <span className="font-medium">2.8 / service</span>
              </div>
              <div className="flex justify-between">
                <span>Mean time to recover</span>
                <span className="font-medium">94s</span>
              </div>
              <div className="flex justify-between">
                <span>Regression suites</span>
                <span className="font-medium">12 passing</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Service profiles</CardTitle>
          <p className="text-xs text-muted-foreground">
            Historical fault survival, weak points, and score trend per service
          </p>
        </CardHeader>
        <CardContent className="space-y-3">
          {demoChaosDna.map((profile) => {
            const Icon = trendIcon[profile.trend]
            return (
              <div key={profile.service} className="rounded-md border border-border p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-medium">{profile.service}</span>
                    <Badge variant="outline">{profile.tier}</Badge>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-2xl font-bold">{profile.resilience_score}</span>
                    <Icon className={`h-4 w-4 ${profile.trend === 'up' ? 'text-success' : profile.trend === 'down' ? 'text-destructive' : 'text-muted-foreground'}`} />
                  </div>
                </div>
                <div className="mt-3 grid gap-2 text-xs sm:grid-cols-2">
                  <div>
                    <p className="text-muted-foreground">Survived</p>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {profile.faults_survived.map((f) => (
                        <Badge key={f} variant="success">{f}</Badge>
                      ))}
                    </div>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Weak points</p>
                    <p className="mt-1 text-foreground">{profile.weak_points.join(' · ')}</p>
                  </div>
                </div>
                <p className="mt-2 text-[10px] text-muted-foreground">Last tested {profile.last_tested}</p>
              </div>
            )
          })}
        </CardContent>
      </Card>

      <Card>
        <CardContent className="flex items-center justify-between p-4">
          <div>
            <p className="text-sm font-medium">Score history export</p>
            <p className="text-xs text-muted-foreground">
              Feed Chaos DNA into quarterly resilience reviews and team scorecards
            </p>
          </div>
          <PhaseBadge status="planned" phase={4} />
        </CardContent>
      </Card>
    </div>
  )
}
