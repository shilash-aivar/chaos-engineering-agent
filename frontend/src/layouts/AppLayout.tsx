import { Outlet } from 'react-router-dom'
import { useEffect } from 'react'
import { useHealth } from '@/hooks/useHealth'
import { useAppStore } from '@/store/appStore'
import { Header } from '@/components/layout/Header'
import { Sidebar } from '@/components/layout/Sidebar'

export function AppLayout() {
  const setApiHealthy = useAppStore((s) => s.setApiHealthy)
  const { isError, isSuccess } = useHealth()

  useEffect(() => {
    if (isSuccess) setApiHealthy(true)
    if (isError) setApiHealthy(false)
  }, [isError, isSuccess, setApiHealthy])

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="app-canvas flex min-w-0 flex-1 flex-col">
        <Header />
        <main className="flex-1 overflow-auto px-6 py-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
