import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from './ui/button'
import { ThemeToggleButton } from './ThemeProvider'

const navLinks = [
  { href: '/', label: 'Home' },
  { href: '/upload', label: 'Analyze CV' },
  { href: '/dashboard', label: 'Dashboard' },
]

export function Navbar() {
  const location = useLocation()
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.4, ease: 'easeOut' }}
      className={cn(
        'sticky top-0 z-50 border-b transition-all duration-300',
        scrolled
          ? 'border-border/50 bg-background/80 backdrop-blur-xl shadow-lg shadow-black/5'
          : 'border-transparent bg-background/50 backdrop-blur-sm',
      )}
    >
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link to="/" className="group flex items-center gap-2">
          <motion.div
            whileHover={{ rotate: -15, scale: 1.1 }}
            className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-violet-600 to-indigo-500 shadow-lg shadow-violet-500/25 transition-shadow group-hover:shadow-violet-500/40"
          >
            <Sparkles className="h-4 w-4 text-white" />
          </motion.div>
          <span className="text-lg font-bold tracking-tight">CVision</span>
        </Link>

        <div className="hidden items-center gap-1 sm:flex">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              to={link.href}
              className="relative px-4 py-2"
            >
              <span
                className={cn(
                  'relative text-sm font-medium transition-colors',
                  location.pathname === link.href
                    ? 'text-primary'
                    : 'text-text-secondary hover:text-text-primary',
                )}
              >
                {link.label}
              </span>
              {location.pathname === link.href && (
                <motion.div
                  layoutId="nav-indicator"
                  className="absolute bottom-0 left-2 right-2 h-0.5 rounded-full bg-primary"
                  transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                />
              )}
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <ThemeToggleButton />
          <Link to="/upload">
            <Button variant="gradient" size="sm">
              Upload CV
            </Button>
          </Link>
        </div>
      </div>
    </motion.nav>
  )
}
