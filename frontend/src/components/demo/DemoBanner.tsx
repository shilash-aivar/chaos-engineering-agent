import { Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'

export function DemoBanner({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'flex items-start gap-3 rounded-lg border border-primary/30 bg-primary/10 px-4 py-3',
        className,
      )}
    >
      <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-primary" />
      <div>
        <p className="text-sm font-medium text-primary">UI preview — sample data</p>
        <p className="text-xs text-muted-foreground">
          End-to-end walkthrough with static data. Explore dedicated pages in the sidebar for each
          feature — backend wiring comes over time. Phase 1 orchestrator is live on Dashboard.
        </p>
      </div>
    </div>
  )
}
