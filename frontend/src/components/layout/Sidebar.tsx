import { NavLink } from 'react-router-dom'
import {
  Activity,
  FlaskConical,
  LayoutDashboard,
  Shield,
  Swords,
  Zap,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAppStore } from '@/store/appStore'

const links = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/experiments', label: 'Experiments', icon: FlaskConical },
  { to: '/new', label: 'New experiment', icon: Zap },
  { to: '/posture', label: 'Posture', icon: Shield },
  { to: '/red-blue', label: 'Red vs Blue', icon: Swords },
]

export function Sidebar() {
  const context = useAppStore((s) => s.context)
  const apiHealthy = useAppStore((s) => s.apiHealthy)

  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-border bg-card">
      <div className="border-b border-border px-5 py-5">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-primary" />
          <div>
            <p className="text-sm font-semibold">Chaos Agent</p>
            <p className="text-xs text-muted-foreground">Resilience platform</p>
          </div>
        </div>
      </div>

      <nav className="flex flex-1 flex-col gap-1 p-3">
        {links.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors',
                isActive
                  ? 'bg-primary/15 text-primary'
                  : 'text-muted-foreground hover:bg-accent hover:text-foreground',
              )
            }
          >
            <Icon className="h-4 w-4" />
            {label}
          </NavLink>
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
