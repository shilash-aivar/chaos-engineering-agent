import { NavLink } from 'react-router-dom'
import {
  Activity,
  BookOpen,
  Dna,
  FlaskConical,
  Gauge,
  GitPullRequest,
  Layers,
  LayoutDashboard,
  Lock,
  Plug,
  Scale,
  Shield,
  Swords,
  Wrench,
  Zap,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAppStore } from '@/store/appStore'

const primaryNav = [
  { to: '/', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: '/experiments', label: 'Experiments', icon: FlaskConical },
  { to: '/new', label: 'Compose', icon: Zap },
  { to: '/observability', label: 'Observability', icon: Activity },
  { to: '/red-blue', label: 'Red vs Blue', icon: Swords },
]

const platformNav = [
  { to: '/posture', label: 'Posture', icon: Shield },
  { to: '/context', label: 'Context', icon: BookOpen },
  { to: '/ci-gate', label: 'CI gate', icon: GitPullRequest },
  { to: '/infrastructure', label: 'Infrastructure', icon: Layers },
  { to: '/remediation', label: 'Remediation', icon: Wrench },
  { to: '/chaos-dna', label: 'Chaos DNA', icon: Dna },
  { to: '/load-testing', label: 'Performance', icon: Gauge },
  { to: '/policies', label: 'Policies', icon: Lock },
  { to: '/referee', label: 'Referee', icon: Scale },
  { to: '/integrations', label: 'Integrations', icon: Plug },
]

function NavGroup({
  title,
  items,
}: {
  title: string
  items: { to: string; label: string; icon: typeof LayoutDashboard; end?: boolean }[]
}) {
  return (
    <div>
      <p className="mb-2 px-3 text-[10px] font-semibold uppercase tracking-[0.12em] text-muted-foreground/70">
        {title}
      </p>
      <div className="flex flex-col gap-0.5">
        {items.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) => cn('nav-item', isActive && 'nav-item--active')}
          >
            <Icon className="h-4 w-4 shrink-0 opacity-80" />
            <span>{label}</span>
          </NavLink>
        ))}
      </div>
    </div>
  )
}

export function Sidebar() {
  const context = useAppStore((s) => s.context)
  const apiHealthy = useAppStore((s) => s.apiHealthy)

  return (
    <aside className="flex w-[15.5rem] shrink-0 flex-col border-r border-border bg-sidebar">
      <div className="border-b border-border px-4 py-5">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/15 ring-1 ring-primary/25">
            <span className="text-sm font-bold text-primary">C</span>
          </div>
          <div className="min-w-0">
            <p className="truncate text-sm font-bold tracking-tight">Chaos Agent</p>
            <p className="text-[11px] text-muted-foreground">Resilience control plane</p>
          </div>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-6 overflow-y-auto p-3">
        <NavGroup title="Operations" items={primaryNav} />
        <NavGroup title="Platform" items={platformNav} />
      </nav>

      <div className="border-t border-border p-4">
        <div className="rounded-lg border border-border bg-card/60 p-3">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
            Environment
          </p>
          <p className="mt-1 truncate text-sm font-medium">{context.cluster}</p>
          <p className="text-xs text-muted-foreground">
            {context.namespace} · {context.environment}
          </p>
          <div className="mt-3 flex items-center justify-between text-[11px]">
            <span
              className={cn(
                'inline-flex items-center gap-1.5 font-medium',
                apiHealthy ? 'text-success' : 'text-destructive',
              )}
            >
              <span
                className={cn(
                  'status-dot',
                  apiHealthy ? 'bg-success' : 'bg-destructive',
                  apiHealthy && 'status-dot--pulse',
                )}
              />
              {apiHealthy ? 'API online' : 'API offline'}
            </span>
            <span className="font-mono text-muted-foreground">{context.aws_region}</span>
          </div>
        </div>
      </div>
    </aside>
  )
}
