import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { demoRedBlue, demoRedBlueTranscript } from '@/demo/mockData'
import { listCampaigns, startCampaign } from '@/api/client'
import { useAppStore } from '@/store/appStore'
import { formatRelativeTime } from '@/lib/utils'
import { DemoRedBlueArena } from '@/components/demo/DemoRedBlueArena'
import { DemoResilienceTrend } from '@/components/demo/DemoResilienceTrend'
import { PreviewBanner, PhaseBadge } from '@/components/shared/PreviewBanner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'

export function RedBluePage() {
  const campaigns = useAppStore((s) => s.campaigns)
  const setCampaigns = useAppStore((s) => s.setCampaigns)
  const [name, setName] = useState('staging-game-day')
  const [loading, setLoading] = useState(true)
  const [starting, setStarting] = useState(false)

  useEffect(() => {
    void listCampaigns()
      .then(setCampaigns)
      .finally(() => setLoading(false))
  }, [setCampaigns])

  const handleStart = async () => {
    setStarting(true)
    try {
      const c = await startCampaign(name)
      setCampaigns([c, ...campaigns.filter((x) => x.id !== c.id)])
    } finally {
      setStarting(false)
    }
  }

  if (loading) return <p className="text-sm text-muted-foreground">Loading campaigns…</p>

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Start campaign</CardTitle>
          <CardDescription>
            Red attacks · Blue defends · Referee scores · Staging only · Max 3 rounds
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-wrap gap-3">
          <Input
            className="max-w-xs"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="Campaign name"
          />
          <Button variant="red" onClick={handleStart} disabled={starting}>
            Start Red vs Blue
          </Button>
        </CardContent>
      </Card>

      <div className="grid gap-4">
        {campaigns.map((c) => (
          <Card key={c.id}>
            <CardContent className="flex flex-wrap items-center justify-between gap-4 p-5">
              <div>
                <p className="font-medium">{c.name}</p>
                <p className="text-xs text-muted-foreground">
                  Round {c.round}/{c.max_rounds} · {formatRelativeTime(c.last_round_at)}
                </p>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-center">
                  <p className="text-xs text-red-team">Red</p>
                  <p className="text-xl font-bold text-red-team">{c.red_score}</p>
                </div>
                <div className="text-center">
                  <p className="text-xs text-blue-team">Blue</p>
                  <p className="text-xl font-bold text-blue-team">{c.blue_score}</p>
                </div>
                <Badge variant={c.leader === 'red' ? 'red' : c.leader === 'blue' ? 'blue' : 'secondary'}>
                  {c.leader === 'draw' ? 'draw' : `${c.leader} leading`}
                </Badge>
                <Badge variant={c.state === 'active' ? 'warning' : 'success'}>{c.state}</Badge>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <PreviewBanner phase={3} liveHint="Campaign list is live — arena, transcripts, and closed-loop scoring are preview below." />

      <div className="grid gap-4 lg:grid-cols-2">
        <DemoRedBlueArena />
        <DemoResilienceTrend />
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-red-team">Red agent transcript</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {demoRedBlueTranscript.red.map((msg, i) => (
              <p key={i} className="rounded-md border border-red-team/20 bg-red-team/5 px-3 py-2 text-xs">
                {msg.text}
              </p>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm text-blue-team">Blue agent transcript</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {demoRedBlueTranscript.blue.map((msg, i) => (
              <p key={i} className="rounded-md border border-blue-team/20 bg-blue-team/5 px-3 py-2 text-xs">
                {msg.text}
              </p>
            ))}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardContent className="p-4">
          <p className="text-sm">
            <span className="font-medium">Referee:</span>{' '}
            <span className="text-muted-foreground">{demoRedBlueTranscript.referee}</span>
          </p>
          <p className="mt-2 text-xs text-muted-foreground">
            Round {demoRedBlue.round}/{demoRedBlue.maxRounds} · equilibrium rounds export to{' '}
            <Link to="/ci-gate" className="text-primary hover:underline">
              regression suites
            </Link>
          </p>
          <PhaseBadge status="planned" phase={4} className="mt-3" />
        </CardContent>
      </Card>
    </div>
  )
}
