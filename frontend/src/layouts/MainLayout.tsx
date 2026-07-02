import { Outlet, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { Footer } from '@/components/Footer'
import { Navbar } from '@/components/Navbar'
import { NebulaBackground } from '@/components/NebulaBackground'

export function MainLayout() {
  const location = useLocation()

  return (
    <div className="relative flex min-h-screen flex-col">
      <NebulaBackground />
      <Navbar />
      <main className="relative z-10 flex-1">
        <AnimatePresence mode="wait">
          <Outlet key={location.pathname} />
        </AnimatePresence>
      </main>
      <Footer />
    </div>
  )
}
