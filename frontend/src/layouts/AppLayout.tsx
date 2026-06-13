import { Outlet } from 'react-router-dom'
import { useEffect } from 'react'
import { getHealth } from '@/api/client'
import { useAppStore } from '@/store/appStore'
import { Header } from '@/components/layout/Header'
import { Sidebar } from '@/components/layout/Sidebar'

export function AppLayout() {
  const setApiHealthy = useAppStore((s) => s.setApiHealthy)

  useEffect(() => {
    const check = () => {
      void getHealth()
        .then(() => setApiHealthy(true))
        .catch(() => setApiHealthy(false))
    }
    check()
    const id = setInterval(check, 15000)
    return () => clearInterval(id)
  }, [setApiHealthy])

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header />
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
