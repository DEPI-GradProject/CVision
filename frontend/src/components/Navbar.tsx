import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Sparkles, LogOut, Menu, X } from 'lucide-react'
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
  const [mobileOpen, setMobileOpen] = useState(false)
  const { isAuthenticated, user, logout } = useAuth()

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20)
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [])

  useEffect(() => {
    setMobileOpen(false)
  }, [location.pathname])

  return (
    <motion.nav
      initial={{ y: -16, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      aria-label="Main navigation"
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
            className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-[#007aff] to-[#005bbf] shadow-md"
          >
            <Sparkles className="h-3.5 w-3.5 text-white" />
          </motion.div>
          <span className="text-base font-bold tracking-tight">CVision</span>
        </Link>

        <div className="hidden items-center gap-1 sm:flex" role="menubar">
          {navLinks.map((link) => (
            <Link
              key={link.href}
              to={link.href}
              role="menuitem"
              aria-current={location.pathname === link.href ? 'page' : undefined}
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
              <Button variant="ghost" size="sm" onClick={logout} aria-label="Log out" className="rounded-full h-8 w-8 p-0">
                <LogOut className="h-3.5 w-3.5" />
              </Button>
            </div>
          ) : (
            <div className="hidden items-center gap-1.5 sm:flex">
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
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label={mobileOpen ? 'Close navigation menu' : 'Open navigation menu'}
            aria-expanded={mobileOpen}
            className="flex sm:hidden rounded-lg p-2 text-text-secondary hover:text-text-primary hover:bg-surface-light/50 transition-colors"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="overflow-hidden border-t border-border/50 bg-white/95 dark:bg-black/95 apple-blur sm:hidden"
          >
            <div className="space-y-1 px-4 py-3">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  to={link.href}
                  aria-current={location.pathname === link.href ? 'page' : undefined}
                  className={cn(
                    'flex items-center rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
                    location.pathname === link.href
                      ? 'bg-primary/10 text-primary'
                      : 'text-text-secondary hover:text-text-primary hover:bg-surface-light/50',
                  )}
                >
                  {link.label}
                </Link>
              ))}
              {!isAuthenticated && (
                <div className="flex gap-2 pt-2 border-t border-border/50 mt-2">
                  <Link to="/login" className="flex-1">
                    <Button variant="outline" size="sm" className="w-full rounded-full text-xs">
                      Sign In
                    </Button>
                  </Link>
                  <Link to="/register" className="flex-1">
                    <Button variant="gradient" size="sm" className="w-full rounded-full text-xs">
                      Sign Up
                    </Button>
                  </Link>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.nav>
  )
}
