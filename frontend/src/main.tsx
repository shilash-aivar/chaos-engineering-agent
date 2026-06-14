import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { RouterProvider } from 'react-router-dom'
import { Toaster } from 'sonner'
import { QueryProvider } from '@/providers/QueryProvider'
import { router } from '@/router'
import '@/styles.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryProvider>
      <RouterProvider router={router} />
      <Toaster richColors position="bottom-right" />
    </QueryProvider>
  </StrictMode>,
)
