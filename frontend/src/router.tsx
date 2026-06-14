import { lazy, Suspense, type ComponentType } from 'react'
import { createBrowserRouter } from 'react-router-dom'
import { AppLayout } from '@/layouts/AppLayout'
import { Skeleton } from '@/components/ui/skeleton'

function PageLoader() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-24 rounded-lg" />
      <Skeleton className="h-80 rounded-lg" />
    </div>
  )
}

function lazyPage(loader: () => Promise<{ default: ComponentType }>) {
  const Page = lazy(loader)
  return (
    <Suspense fallback={<PageLoader />}>
      <Page />
    </Suspense>
  )
}

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: lazyPage(() => import('@/pages/DashboardPage').then((m) => ({ default: m.DashboardPage }))) },
      { path: 'experiments', element: lazyPage(() => import('@/pages/ExperimentsPage').then((m) => ({ default: m.ExperimentsPage }))) },
      { path: 'experiments/:id', element: lazyPage(() => import('@/pages/ExperimentDetailPage').then((m) => ({ default: m.ExperimentDetailPage }))) },
      { path: 'new', element: lazyPage(() => import('@/pages/NewExperimentPage').then((m) => ({ default: m.NewExperimentPage }))) },
      { path: 'infrastructure', element: lazyPage(() => import('@/pages/InfrastructurePage').then((m) => ({ default: m.InfrastructurePage }))) },
      { path: 'context', element: lazyPage(() => import('@/pages/ContextPage').then((m) => ({ default: m.ContextPage }))) },
      { path: 'remediation', element: lazyPage(() => import('@/pages/RemediationPage').then((m) => ({ default: m.RemediationPage }))) },
      { path: 'chaos-dna', element: lazyPage(() => import('@/pages/ChaosDnaPage').then((m) => ({ default: m.ChaosDnaPage }))) },
      { path: 'posture', element: lazyPage(() => import('@/pages/PosturePage').then((m) => ({ default: m.PosturePage }))) },
      { path: 'red-blue', element: lazyPage(() => import('@/pages/RedBluePage').then((m) => ({ default: m.RedBluePage }))) },
      { path: 'ci-gate', element: lazyPage(() => import('@/pages/CiGatePage').then((m) => ({ default: m.CiGatePage }))) },
      { path: 'policies', element: lazyPage(() => import('@/pages/PoliciesPage').then((m) => ({ default: m.PoliciesPage }))) },
      { path: 'referee', element: lazyPage(() => import('@/pages/RefereePage').then((m) => ({ default: m.RefereePage }))) },
      { path: 'integrations', element: lazyPage(() => import('@/pages/IntegrationsPage').then((m) => ({ default: m.IntegrationsPage }))) },
      { path: 'observability', element: lazyPage(() => import('@/pages/ObservabilityPage').then((m) => ({ default: m.ObservabilityPage }))) },
      { path: 'load-testing', element: lazyPage(() => import('@/pages/LoadTestingPage').then((m) => ({ default: m.LoadTestingPage }))) },
      { path: 'demo', element: lazyPage(() => import('@/pages/DemoPage').then((m) => ({ default: m.DemoPage }))) },
      { path: 'roadmap', element: lazyPage(() => import('@/pages/RoadmapPage').then((m) => ({ default: m.RoadmapPage }))) },
    ],
  },
])
