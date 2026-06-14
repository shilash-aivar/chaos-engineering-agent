import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

type StatCardProps = {
  icon: LucideIcon
  label: string
  value: string | number
  hint?: string
  accent?: 'amber' | 'teal' | 'rose' | 'sky' | 'neutral'
}

const accentColor: Record<NonNullable<StatCardProps['accent']>, string> = {
  amber: 'text-primary',
  teal: 'text-success',
  rose: 'text-red-team',
  sky: 'text-blue-team',
  neutral: 'text-muted-foreground',
}

export function StatCard({ icon: Icon, label, value, hint, accent = 'neutral' }: StatCardProps) {
  const color = accentColor[accent]
  return (
    <div className="stat-tile">
      <span className={cn('stat-tile__icon', color)}>
        <Icon className="h-4 w-4" />
      </span>
      <div className="min-w-0">
        <p className="stat-tile__value">{value}</p>
        <p className="stat-tile__label">{label}</p>
        {hint && <p className="mt-0.5 text-[10px] text-muted-foreground/80">{hint}</p>}
      </div>
    </div>
  )
}

type PageHeaderProps = {
  title: string
  description?: string
  action?: ReactNode
  badge?: ReactNode
}

export function PageHeader({ title, description, action, badge }: PageHeaderProps) {
  return (
    <header className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
      <div className="space-y-1.5">
        <div className="flex flex-wrap items-center gap-2">
          <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
          {badge}
        </div>
        {description && (
          <p className="max-w-2xl text-sm leading-relaxed text-muted-foreground">{description}</p>
        )}
      </div>
      {action && <div className="flex shrink-0 items-center gap-2">{action}</div>}
    </header>
  )
}

export function PageShell({ children }: { children: ReactNode }) {
  return <div className="anim-page-enter mx-auto w-full max-w-6xl">{children}</div>
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon
  title: string
  description: string
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border px-8 py-14 text-center">
      <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-muted text-muted-foreground">
        <Icon className="h-5 w-5" />
      </div>
      <p className="text-sm font-semibold">{title}</p>
      <p className="mt-1 max-w-sm text-sm text-muted-foreground">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}
