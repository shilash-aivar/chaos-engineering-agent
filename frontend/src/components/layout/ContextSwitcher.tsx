import { useAppStore, contextOptions } from '@/store/appStore'
import { cn } from '@/lib/utils'

export function ContextSwitcher({ className }: { className?: string }) {
  const context = useAppStore((s) => s.context)
  const setContext = useAppStore((s) => s.setContext)

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <label htmlFor="context-select" className="sr-only">
        Target context
      </label>
      <select
        id="context-select"
        value={context.id}
        onChange={(e) => {
          const next = contextOptions.find((c) => c.id === e.target.value)
          if (next) setContext(next)
        }}
        className="h-8 max-w-[220px] rounded-md border border-border bg-card px-2 text-xs text-foreground outline-none focus:ring-1 focus:ring-ring"
      >
        {contextOptions.map((opt) => (
          <option key={opt.id} value={opt.id}>
            {opt.label}
          </option>
        ))}
      </select>
      {context.environment === 'production' && (
        <span className="rounded-full border border-warning/40 bg-warning/15 px-2 py-0.5 text-[10px] font-medium text-warning">
          prod gate
        </span>
      )}
    </div>
  )
}
