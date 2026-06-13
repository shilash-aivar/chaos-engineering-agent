import { useLocation } from 'react-router-dom'

const titles: Record<string, string> = {
  '/': 'Dashboard',
  '/experiments': 'Experiments',
  '/new': 'New experiment',
  '/infrastructure': 'Infrastructure',
  '/remediation': 'Remediation',
  '/chaos-dna': 'Chaos DNA',
  '/posture': 'Posture scan',
  '/red-blue': 'Red vs Blue',
  '/ci-gate': 'CI resilience gate',
  '/policies': 'Safety policies',
  '/integrations': 'Integrations',
  '/observability': 'Observability',
  '/load-testing': 'Load testing',
  '/demo': 'UI walkthrough',
  '/roadmap': 'Product roadmap',
}

export function Header() {
  const { pathname } = useLocation()
  const base = '/' + (pathname.split('/').filter(Boolean)[0] ?? '')
  const title = titles[base] ?? 'Experiment detail'

  return (
    <header className="flex h-14 items-center justify-between border-b border-border px-6">
      <h1 className="text-lg font-semibold">{title}</h1>
      <p className="text-xs text-muted-foreground">Internal · staging-first · auto-rollback enabled</p>
    </header>
  )
}
