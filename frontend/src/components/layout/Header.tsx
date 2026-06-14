import { Link, useLocation, useParams } from 'react-router-dom'
import { ChevronRight, Plus } from 'lucide-react'
import { ContextSwitcher } from '@/components/layout/ContextSwitcher'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useAppStore } from '@/store/appStore'

const crumbs: Record<string, string> = {
  '': 'Overview',
  experiments: 'Experiments',
  new: 'Compose experiment',
  infrastructure: 'Infrastructure',
  context: 'Context',
  remediation: 'Remediation',
  'chaos-dna': 'Chaos DNA',
  'red-blue': 'Red vs Blue',
  posture: 'Posture',
  'ci-gate': 'CI gate',
  policies: 'Policies',
  referee: 'Referee',
  integrations: 'Integrations',
  observability: 'Observability',
  'load-testing': 'Performance',
  demo: 'Walkthrough',
  roadmap: 'Roadmap',
}

export function Header() {
  const { pathname } = useLocation()
  const { id } = useParams()
  const context = useAppStore((s) => s.context)
  const segments = pathname.split('/').filter(Boolean)
  const root = segments[0] ?? ''
  const pageTitle = id && root === 'experiments' ? 'Experiment run' : crumbs[root] ?? 'Overview'

  return (
    <header className="sticky top-0 z-20 flex h-14 items-center justify-between gap-4 border-b border-border bg-background/80 px-6 backdrop-blur-md">
      <div className="flex min-w-0 items-center gap-2 text-sm">
        <Link to="/" className="text-muted-foreground transition-colors hover:text-foreground">
          Home
        </Link>
        {segments.length > 0 && (
          <>
            <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground/60" />
            <span className="truncate font-medium">{pageTitle}</span>
          </>
        )}
        <Badge variant="outline" className="ml-2 hidden font-mono text-[10px] sm:inline-flex">
          {context.environment}
        </Badge>
      </div>

      <div className="flex items-center gap-3">
        <ContextSwitcher />
        <Button size="sm" className="hidden sm:inline-flex" asChild>
          <Link to="/new">
            <Plus className="h-3.5 w-3.5" />
            New experiment
          </Link>
        </Button>
      </div>
    </header>
  )
}
