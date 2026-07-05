import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Sparkles, LogOut } from 'lucide-react'
import { cn } from '@/lib/utils'
import { Button } from './ui/button'
import { ThemeToggleButton } from './ThemeProvider'
import { useAuth } from '@/contexts/AuthContext'

const navLinks = [
  { href: '/', label: 'Home' },
  { href: '/upload', label: 'Analyze CV' },
  { href: '/match-job', label: 'Job Match' },
  { href: '/dashboard', label: 'Dashboard' },
]

export function Navbar() {
  const location = useLocation()
  const [scrolled, setScrolled] = useState(false)
  const { isAuthenticated, user, logout } = useAuth()

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  return (
    <motion.nav
      initial={{ y: -16, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className={cn(
        'fixed top-0 left-0 right-0 z-50 transition-all duration-300',
        scrolled
          ? 'bg-white/70 dark:bg-black/70 apple-blur border-b border-border/50 shadow-glass dark:shadow-glass-dark'
          : 'bg-transparent',
      )}
    >
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <Link to="/" className="group flex items-center gap-2.5">
          <motion.div
            whileHover={{ rotate: -10, scale: 1.05 }}
            className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-violet-600 to-indigo-500 shadow-md"
          >
            <Sparkles className="h-3.5 w-3.5 text-white" />
          </motion.div>
          <span className="text-base font-bold tracking-tight">CVision</span>
        </Link>

        <div className="hidden items-center gap-1 sm:flex">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              to={link.href}
              className="relative px-3.5 py-1.5"
            >
              <span
                className={cn(
                  'relative text-xs font-medium tracking-wide transition-colors',
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
                  className="absolute -bottom-0.5 left-3.5 right-3.5 h-0.5 rounded-full bg-primary"
                  transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                />
              )}
            </Link>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <ThemeToggleButton />
          {isAuthenticated ? (
            <div className="flex items-center gap-2">
              <span className="hidden text-xs text-text-secondary md:block">{user?.email}</span>
              <Button variant="ghost" size="sm" onClick={logout} className="rounded-full h-8 w-8 p-0">
                <LogOut className="h-3.5 w-3.5" />
              </Button>
            </div>
          ) : (
            <div className="flex items-center gap-1.5">
              <Link to="/login">
                <Button variant="ghost" size="sm" className="rounded-full text-xs h-8 px-4">
                  Sign In
                </Button>
              </Link>
              <Link to="/register">
                <Button variant="gradient" size="sm" className="rounded-full text-xs h-8 px-4">
                  Sign Up
                </Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </motion.nav>
  )
}
