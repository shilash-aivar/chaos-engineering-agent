export function SecurityDisclaimer({
  className = '',
  compact = false,
}: {
  className?: string
  compact?: boolean
}) {
  return (
    <p
      className={`rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-muted-foreground ${compact ? 'mb-4' : 'mb-6'} ${className}`}
    >
      <span className="font-medium text-foreground">Note:</span> Example CVEs in attack plans are{' '}
      <strong>illustrative vulnerability classes</strong>, not confirmed findings in your environment.
      Staging-only probes. Install <code className="text-[10px]">tfsec</code> /{' '}
      <code className="text-[10px]">semgrep</code> for live SAST when available.
    </p>
  )
}
