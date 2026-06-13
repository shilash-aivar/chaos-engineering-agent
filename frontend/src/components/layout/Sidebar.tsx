import { NavLink } from 'react-router-dom'
import {
  Activity,
  Cloud,
  Dna,
  FlaskConical,
  Gauge,
  GitPullRequest,
  Layers,
  LayoutDashboard,
  Lock,
  Map,
  Plug,
  Presentation,
  Shield,
  Swords,
  Wrench,
  Zap,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAppStore } from '@/store/appStore'
import { PhaseBadge } from '@/components/shared/PreviewBanner'
import type { FeatureStatus } from '@/types'

type NavItem = {
  to: string
  label: string
  icon: typeof LayoutDashboard
  status?: FeatureStatus
}

type NavSection = {
  title: string
  items: NavItem[]
}

const sections: NavSection[] = [
  {
    title: 'Operate',
    items: [
      { to: '/', label: 'Dashboard', icon: LayoutDashboard, status: 'live' },
      { to: '/experiments', label: 'Experiments', icon: FlaskConical, status: 'live' },
      { to: '/new', label: 'New experiment', icon: Zap, status: 'live' },
    ],
  },
  {
    title: 'Intelligence',
    items: [
      { to: '/infrastructure', label: 'Infrastructure', icon: Layers, status: 'preview' },
      { to: '/remediation', label: 'Remediation', icon: Wrench, status: 'preview' },
      { to: '/chaos-dna', label: 'Chaos DNA', icon: Dna, status: 'preview' },
      { to: '/red-blue', label: 'Red vs Blue', icon: Swords, status: 'preview' },
    ],
  },
  {
    title: 'Platform',
    items: [
      { to: '/posture', label: 'Posture', icon: Shield, status: 'live' },
      { to: '/ci-gate', label: 'CI gate', icon: GitPullRequest, status: 'preview' },
      { to: '/policies', label: 'Policies', icon: Lock, status: 'preview' },
      { to: '/integrations', label: 'Integrations', icon: Plug, status: 'preview' },
      { to: '/observability', label: 'Observability', icon: Activity, status: 'preview' },
      { to: '/load-testing', label: 'Load testing', icon: Gauge, status: 'preview' },
    ],
  },
  {
    title: 'Vision',
    items: [
      { to: '/demo', label: 'UI walkthrough', icon: Presentation, status: 'preview' },
      { to: '/roadmap', label: 'Roadmap', icon: Map, status: 'preview' },
    ],
  },
]

export function Sidebar() {
  const context = useAppStore((s) => s.context)
  const apiHealthy = useAppStore((s) => s.apiHealthy)

  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-border bg-card">
      <div className="border-b border-border px-5 py-5">
        <div className="flex items-center gap-2">
          <Cloud className="h-5 w-5 text-primary" />
          <div>
            <p className="text-sm font-semibold">Chaos Agent</p>
            <p className="text-xs text-muted-foreground">K8s + AWS resilience</p>
          </div>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-4 overflow-y-auto p-3">
        {sections.map((section) => (
          <div key={section.title}>
            <p className="mb-1 px-3 text-[10px] font-medium uppercase tracking-wider text-muted-foreground">
              {section.title}
            </p>
            <div className="flex flex-col gap-0.5">
              {section.items.map(({ to, label, icon: Icon, status }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={to === '/'}
                  className={({ isActive }) =>
                    cn(
                      'flex items-center justify-between gap-2 rounded-md px-3 py-2 text-sm transition-colors',
                      isActive
                        ? 'bg-primary/15 text-primary'
                        : 'text-muted-foreground hover:bg-accent hover:text-foreground',
                    )
                  }
                >
                  <span className="flex items-center gap-2">
                    <Icon className="h-4 w-4 shrink-0" />
                    {label}
                  </span>
                  {status && status !== 'live' && (
                    <PhaseBadge status={status} className="scale-90" />
                  )}
                </NavLink>
              ))}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-border p-4 text-xs text-muted-foreground">
        <p className="font-medium text-foreground">{context.cluster}</p>
        <p>{context.namespace} · {context.environment}</p>
        <p className="mt-2 flex items-center gap-1.5">
          <span
            className={cn(
              'h-2 w-2 rounded-full',
              apiHealthy ? 'bg-success' : 'bg-destructive',
            )}
          />
          API {apiHealthy ? 'connected' : 'offline'}
        </p>
      </div>
    </aside>
  )
}
