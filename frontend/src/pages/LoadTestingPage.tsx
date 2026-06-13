import { demoLoadTests } from '@/demo/mockData'
import { PreviewBanner, PhaseBadge } from '@/components/shared/PreviewBanner'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'

export function LoadTestingPage() {
  return (
    <div className="space-y-6">
      <PreviewBanner phase={2} liveHint="k6 executor will pair load with fault injection in the same experiment plan." />

      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <div>
            <CardTitle className="text-sm">k6 scenarios</CardTitle>
            <p className="text-xs text-muted-foreground">
              Load runs in parallel with Chaos Mesh / Toxiproxy faults
            </p>
          </div>
          <Button size="sm" disabled>
            New scenario
          </Button>
        </CardHeader>
        <CardContent className="space-y-3">
          {demoLoadTests.map((scenario) => (
            <div key={scenario.id} className="rounded-md border border-border p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div>
                  <p className="font-medium">{scenario.name}</p>
                  <p className="text-xs text-muted-foreground">
                    target={scenario.target} · {scenario.vus} VUs · {scenario.duration} · ramp {scenario.ramp}
                  </p>
                </div>
                <Badge variant="outline">k6</Badge>
              </div>
              {scenario.last_result ? (
                <div className="mt-3 grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="rounded border border-border p-2">
                    <p className="text-muted-foreground">RPS</p>
                    <p className="font-bold">{scenario.last_result.rps}</p>
                  </div>
                  <div className="rounded border border-border p-2">
                    <p className="text-muted-foreground">p99</p>
                    <p className="font-bold">{scenario.last_result.p99_ms}ms</p>
                  </div>
                  <div className="rounded border border-border p-2">
                    <p className="text-muted-foreground">Errors</p>
                    <p className={`font-bold ${scenario.last_result.errors_pct > 1 ? 'text-destructive' : ''}`}>
                      {scenario.last_result.errors_pct}%
                    </p>
                  </div>
                </div>
              ) : (
                <p className="mt-2 text-xs text-muted-foreground">Not run yet</p>
              )}
              <div className="mt-3 flex gap-2">
                <Button variant="outline" size="sm" disabled>
                  Edit script
                </Button>
                <Button variant="outline" size="sm" disabled>
                  Pair with experiment
                </Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Example k6 script snippet</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="overflow-auto rounded-md border border-border bg-muted p-4 text-xs">{`import http from 'k6/http';
import { check } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 120 },
    { duration: '5m', target: 120 },
    { duration: '30s', target: 0 },
  ],
};

export default function () {
  const res = http.get('https://checkout.staging/health');
  check(res, { 'status is 200': (r) => r.status === 200 });
}`}</pre>
          <div className="mt-3 flex items-center gap-2">
            <PhaseBadge status="preview" phase={2} />
            <span className="text-xs text-muted-foreground">Executor applies script via k6 Job in experiment namespace</span>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
