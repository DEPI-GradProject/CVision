import { useState, useEffect } from 'react'
import { Outlet, useLocation, useNavigate, Link } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import {
  Home,
  FileText,
  BarChart3,
  Briefcase,
  Bell,
  Sun,
  Moon,
  LogOut,
  Sparkles,
  TrendingUp,
  Clock,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAuth } from '@/contexts/AuthContext'
import { useTheme } from '@/components/ThemeProvider'
import { api } from '@/api/client'
import type { DashboardStats } from '@/types'

const navItems = [
  { href: '/', label: 'Home', icon: Home },
  { href: '/upload', label: 'Analyze CV', icon: FileText },
  { href: '/match-job', label: 'Job Match', icon: Briefcase },
  { href: '/dashboard', label: 'Dashboard', icon: BarChart3 },
]

const mobileNavItems = [
  { href: '/', label: 'Home', icon: Home },
  { href: '/upload', label: 'Analyze', icon: FileText },
  { href: '/match-job', label: 'Match', icon: Briefcase },
  { href: '/dashboard', label: 'Dashboard', icon: BarChart3 },
]

function QuickStats() {
  const [stats, setStats] = useState<DashboardStats | null>(null)

  useEffect(() => {
    api.getStats()
      .then((r) => setStats(r.data))
      .catch(() => {})
  }, [])

  if (!stats) return null

  const items = [
    { label: 'CVs Analyzed', value: stats.total_analyses, icon: FileText },
    { label: 'Avg ATS Score', value: stats.average_score, icon: TrendingUp },
    { label: 'Jobs Matched', value: stats.total_job_matches, icon: Briefcase },
  ]

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item.label} className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary/10">
              <item.icon className="h-3.5 w-3.5 text-primary" />
            </div>
            <span className="text-xs text-text-secondary">{item.label}</span>
          </div>
          <span className="text-xs font-semibold text-primary">{item.value}</span>
        </div>
      ))}
    </div>
  )
}

function UserSection() {
  const { user, logout } = useAuth()
  const { theme, toggle } = useTheme()

  return (
    <div className="space-y-3">
      <button
        onClick={toggle}
        className="flex w-full items-center justify-between rounded-xl border border-border bg-surface-light px-3 py-2.5 text-xs transition-colors hover:bg-border/50"
      >
        <span className="text-text-secondary">{theme === 'dark' ? 'Dark Mode' : 'Light Mode'}</span>
        <div className={cn(
          'relative h-5 w-9 rounded-full transition-colors',
          theme === 'dark' ? 'bg-primary' : 'bg-border',
        )}>
          <motion.div
            layout
            transition={{ type: 'spring', stiffness: 500, damping: 30 }}
            className={cn(
              'absolute top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-white shadow-sm',
              theme === 'dark' ? 'left-[18px]' : 'left-0.5',
            )}
          >
            {theme === 'dark' ? (
              <Moon className="h-2.5 w-2.5 text-primary" />
            ) : (
              <Sun className="h-2.5 w-2.5 text-amber-500" />
            )}
          </motion.div>
        </div>
      </button>

      {user && (
        <div className="flex items-center gap-2.5 rounded-xl bg-surface-light/50 px-3 py-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-primary text-xs font-bold text-white">
            {user.email.charAt(0).toUpperCase()}
          </div>
          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-text-primary">{user.email.split('@')[0]}</p>
            <p className="truncate text-[10px] text-text-muted">{user.email}</p>
          </div>
          <button
            onClick={logout}
            className="flex h-6 w-6 items-center justify-center rounded-lg text-text-muted hover:bg-error/10 hover:text-error transition-colors"
          >
            <LogOut className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
    </div>
  )
}

function Sidebar() {
  const location = useLocation()

  return (
    <aside className="hidden md:flex md:w-[210px] md:flex-col md:fixed md:inset-y-0 md:z-40">
      <div className="flex flex-1 flex-col border-r border-border bg-[var(--color-sidebar)] px-3 py-5">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 px-2 mb-7">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-sm font-bold text-white shadow-sm">
            CV
          </div>
          <div>
            <p className="text-sm font-bold leading-tight text-text-primary">CVision</p>
            <p className="text-[10px] text-text-muted leading-tight">AI-Powered Analysis</p>
          </div>
        </Link>

        {/* Navigation */}
        <div className="mb-6">
          <p className="px-2 text-[10px] font-semibold tracking-widest text-text-muted mb-2 uppercase">
            Navigation
          </p>
          <nav className="space-y-0.5">
            {navItems.map((item) => {
              const isActive = location.pathname === item.href
              const Icon = item.icon
              return (
                <Link
                  key={item.href}
                  to={item.href}
                  className={cn(
                    'flex items-center gap-2.5 rounded-xl px-3 py-2.5 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary/10 text-primary'
                      : 'text-text-secondary hover:bg-surface-light hover:text-text-primary',
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              )
            })}
          </nav>
        </div>

        {/* Quick Stats */}
        <div className="mb-6">
          <p className="px-2 text-[10px] font-semibold tracking-widest text-text-muted mb-2 uppercase">
            Quick Stats
          </p>
          <QuickStats />
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* User & Theme */}
        <UserSection />
      </div>
    </aside>
  )
}

function MobileBottomNav() {
  const location = useLocation()

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 border-t border-border bg-[var(--color-sidebar)] md:hidden">
      <div className="flex items-center justify-around py-1.5">
        {mobileNavItems.map((item) => {
          const isActive = location.pathname === item.href
          const Icon = item.icon
          return (
            <Link
              key={item.href}
              to={item.href}
              className="flex flex-col items-center gap-0.5 px-3 py-1"
            >
              <Icon className={cn('h-5 w-5', isActive ? 'text-primary' : 'text-text-muted')} />
              <span className={cn('text-[10px] font-medium', isActive ? 'text-primary' : 'text-text-muted')}>
                {item.label}
              </span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}

function MobileTopBar() {
  const { theme, toggle } = useTheme()
  const { user } = useAuth()

  return (
    <div className="sticky top-0 z-30 flex items-center justify-between border-b border-border bg-[var(--color-sidebar)] px-4 py-3 md:hidden">
      <Link to="/" className="flex items-center gap-2">
        <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-primary text-xs font-bold text-white">
          CV
        </div>
        <span className="text-sm font-bold text-text-primary">CVision</span>
      </Link>
      <div className="flex items-center gap-2">
        <button
          onClick={toggle}
          className="relative h-6 w-11 rounded-full transition-colors"
          style={{ backgroundColor: theme === 'dark' ? '#2563eb' : '#e5e7eb' }}
        >
          <motion.div
            layout
            transition={{ type: 'spring', stiffness: 500, damping: 30 }}
            className={cn(
              'absolute top-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-white shadow-sm',
              theme === 'dark' ? 'left-[22px]' : 'left-0.5',
            )}
          >
            {theme === 'dark' ? (
              <Moon className="h-3 w-3 text-primary" />
            ) : (
              <Sun className="h-3 w-3 text-amber-500" />
            )}
          </motion.div>
        </button>
        <Bell className="h-5 w-5 text-text-muted" />
        {user && (
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-white">
            {user.email.charAt(0).toUpperCase()}
          </div>
        )}
      </div>
    </div>
  )
}

function TopBreadcrumb() {
  const location = useLocation()
  const { user, logout } = useAuth()

  const pageName = (() => {
    switch (location.pathname) {
      case '/': return 'Home'
      case '/upload': return 'Analyze CV'
      case '/match-job': return 'Job Match'
      case '/dashboard': return 'Dashboard'
      default: return ''
    }
  })()

  return (
    <div className="hidden md:flex items-center justify-between mb-6">
      <div className="flex items-center gap-2 text-sm text-text-muted">
        <span>CVision</span>
        {pageName && (
          <>
            <span>/</span>
            <span className="text-text-primary font-medium">{pageName}</span>
          </>
        )}
      </div>
      <div className="flex items-center gap-3">
        <Bell className="h-5 w-5 text-text-muted hover:text-text-primary cursor-pointer transition-colors" />
        {user && (
          <button
            onClick={logout}
            className="flex items-center gap-2 rounded-full bg-surface-light px-3 py-1.5 text-xs text-text-secondary hover:bg-border/50 transition-colors"
          >
            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary text-[9px] font-bold text-white">
              {user.email.charAt(0).toUpperCase()}
            </div>
            {user.email}
            <LogOut className="h-3 w-3" />
          </button>
        )}
      </div>
    </div>
  )
}

export function SidebarLayout() {
  const location = useLocation()

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <MobileTopBar />
      <MobileBottomNav />

      <div className="md:pl-[210px]">
        <main className="min-h-screen px-4 pb-20 pt-4 md:px-8 md:pb-8 md:pt-6">
          <TopBreadcrumb />
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.15, ease: 'easeOut' }}
            >
              <Outlet />
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}
