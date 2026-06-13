import { createBrowserRouter } from 'react-router-dom'
import { AppLayout } from '@/layouts/AppLayout'
import { ChaosDnaPage } from '@/pages/ChaosDnaPage'
import { CiGatePage } from '@/pages/CiGatePage'
import { DemoPage } from '@/pages/DemoPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { ExperimentsPage } from '@/pages/ExperimentsPage'
import { ExperimentDetailPage } from '@/pages/ExperimentDetailPage'
import { InfrastructurePage } from '@/pages/InfrastructurePage'
import { IntegrationsPage } from '@/pages/IntegrationsPage'
import { LoadTestingPage } from '@/pages/LoadTestingPage'
import { NewExperimentPage } from '@/pages/NewExperimentPage'
import { ObservabilityPage } from '@/pages/ObservabilityPage'
import { PoliciesPage } from '@/pages/PoliciesPage'
import { PosturePage } from '@/pages/PosturePage'
import { RedBluePage } from '@/pages/RedBluePage'
import { RemediationPage } from '@/pages/RemediationPage'
import { RoadmapPage } from '@/pages/RoadmapPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'experiments', element: <ExperimentsPage /> },
      { path: 'experiments/:id', element: <ExperimentDetailPage /> },
      { path: 'new', element: <NewExperimentPage /> },
      { path: 'infrastructure', element: <InfrastructurePage /> },
      { path: 'remediation', element: <RemediationPage /> },
      { path: 'chaos-dna', element: <ChaosDnaPage /> },
      { path: 'posture', element: <PosturePage /> },
      { path: 'red-blue', element: <RedBluePage /> },
      { path: 'ci-gate', element: <CiGatePage /> },
      { path: 'policies', element: <PoliciesPage /> },
      { path: 'integrations', element: <IntegrationsPage /> },
      { path: 'observability', element: <ObservabilityPage /> },
      { path: 'load-testing', element: <LoadTestingPage /> },
      { path: 'demo', element: <DemoPage /> },
      { path: 'roadmap', element: <RoadmapPage /> },
    ],
  },
])
