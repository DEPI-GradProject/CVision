import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BarChart3,
  Briefcase,
  Clock,
  ExternalLink,
  FileText,
  Search,
  Sparkles,
  TrendingUp,
  LineChart,
  Loader2,
  X,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'
import { Line } from 'react-chartjs-2'
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip as ChartTooltip, Filler } from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, ChartTooltip, Filler)
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AnimatedPage } from '@/components/AnimatedPage'
import { ScrollReveal } from '@/components/ScrollReveal'
import { cn } from '@/lib/utils'
import { staggerContainer, staggerItem, staggerList, staggerListItem } from '@/lib/animations'
import { api, ApiError } from '@/api/client'
import type { AnalysisHistory, DashboardStats, RawJob } from '@/types'

function CountUp({ value, duration = 1000 }: { value: string; duration?: number }) {
  const [count, setCount] = useState(0)
  const [show, setShow] = useState(false)
  const num = parseInt(value)

  useEffect(() => {
    setShow(true) // eslint-disable-line react-hooks/set-state-in-effect
    let start = 0
    const step = 16
    const totalSteps = duration / step
    const increment = num / totalSteps

    const timer = setInterval(() => {
      start += increment
      if (start >= num) {
        setCount(num)
        clearInterval(timer)
      } else {
        setCount(Math.round(start))
      }
    }, step)

    return () => clearInterval(timer)
  }, [num, duration])

  if (isNaN(num)) {
    return <span className="text-2xl font-bold">{value}</span>
  }

  return (
    <motion.span
      className="text-2xl font-bold"
      initial={{ opacity: 0, y: 10 }}
      animate={show ? { opacity: 1, y: 0 } : {}}
    >
      {count}
      {value.replace(/\d/g, '')}
    </motion.span>
  )
}

interface PersistedJobItem {
  job_title: string
  job_link: string
  platform: string
  published_date?: string
}

function PersistedJobs({ jobs, skills }: { jobs: PersistedJobItem[]; skills: string[] }) {
  const [page, setPage] = useState(0)
  const perPage = 10
  const totalPages = Math.max(1, Math.ceil(jobs.length / perPage))
  const safePage = Math.min(page, totalPages - 1)
  const start = safePage * perPage
  const pageJobs = jobs.slice(start, start + perPage)

  return (
    <div className="space-y-2">
      {pageJobs.map((job, i) => (
        <div
          key={start + i}
          className="flex items-center gap-3 rounded-lg border border-border/60 bg-surface-light/30 p-3"
        >
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium truncate">{job.job_title}</p>
            <div className="flex items-center gap-2 mt-0.5">
              <Badge variant="default" className="rounded-full text-[10px] px-2 py-0">
                {job.platform}
              </Badge>
              {job.published_date && (
                <span className="text-[10px] text-text-muted">
                  {new Date(job.published_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                </span>
              )}
            </div>
          </div>
          <a
            href={job.job_link}
            target="_blank"
            rel="noopener noreferrer"
            className="shrink-0 text-xs font-medium text-primary hover:underline whitespace-nowrap"
          >
            Apply &rarr;
          </a>
        </div>
      ))}
      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 pt-1">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={safePage === 0}
            className="px-2.5 py-1 text-[10px] font-medium rounded-lg border border-border transition disabled:opacity-30 hover:border-primary/50"
          >
            Previous
          </button>
          {Array.from({ length: totalPages }, (_, i) => (
            <button
              key={i}
              onClick={() => setPage(i)}
              className={cn(
                'w-7 h-7 text-[10px] font-medium rounded-lg border transition',
                i === safePage
                  ? 'border-primary bg-primary/10 text-primary'
                  : 'border-border hover:border-primary/50 text-text-muted',
              )}
            >
              {i + 1}
            </button>
          ))}
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={safePage === totalPages - 1}
            className="px-2.5 py-1 text-[10px] font-medium rounded-lg border border-border transition disabled:opacity-30 hover:border-primary/50"
          >
            Next
          </button>
        </div>
      )}
      {skills.length > 0 && (
        <a
          href={`https://www.linkedin.com/jobs/search/?keywords=${encodeURIComponent(skills.slice(0, 3).join(' '))}`}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-1.5 rounded-lg border border-border/50 py-2 text-xs text-text-muted hover:text-primary hover:border-primary/30 transition-colors"
        >
          <ExternalLink className="h-3 w-3" />
          Search live jobs on LinkedIn
        </a>
      )}
    </div>
  )
}

export function DashboardPage() {
  const navigate = useNavigate()
  const [history, setHistory] = useState<AnalysisHistory[]>([])
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)
  const [showJobs, setShowJobs] = useState(false)
  const [expandedId, setExpandedId] = useState<number | null>(null)
  const [jobsCache, setJobsCache] = useState<Map<number, RawJob[]>>(new Map())
  const [jobsLoading, setJobsLoading] = useState<Set<number>>(new Set())

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const histRes = await api.getHistory(50)
        if (cancelled) return
        setHistory(histRes.data)
      } catch (err) {
        if (cancelled) return
        if (err instanceof ApiError && err.status === 401) {
          navigate('/login')
          return
        }
      }
      try {
        if (cancelled) return
        const statsRes = await api.getStats()
        if (cancelled) return
        setStats(statsRes.data)
      } catch {
        if (cancelled) return
        setStats({ total_analyses: 0, average_score: 0, total_job_matches: 0, last_analysis: 'N/A' })
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => { cancelled = true }
  }, [navigate])

  const filtered = history.filter((h) =>
    h.filename.toLowerCase().includes(search.toLowerCase()),
  )

  const statDefs = stats
    ? [
        { label: 'CVs Analyzed', value: String(stats.total_analyses), icon: FileText, color: 'text-[#007aff] bg-[#007aff]/10' },
        { label: 'Average Score', value: String(stats.average_score), icon: BarChart3, color: 'text-[#34c759] bg-[#34c759]/10' },
        { label: 'Jobs Matched', value: String(stats.total_job_matches), icon: TrendingUp, color: 'text-[#ff9500] bg-[#ff9500]/10' },
        { label: 'Last Analysis', value: stats.last_analysis, icon: Clock, color: 'text-[#af52de] bg-[#af52de]/10' },
      ]
    : []

  const handleRowClick = async (h: AnalysisHistory) => {
    if (expandedId === h.id) {
      setExpandedId(null)
      return
    }
    setExpandedId(h.id)
    if (jobsCache.has(h.id)) return
    setJobsLoading((prev) => new Set(prev).add(h.id))
    try {
      const res = await api.getLatestJobs(50)
      const skillsLower = h.skills_extracted.map((s) => s.toLowerCase())
      const matched = res.data.filter((job) => {
        const searchText = `${job.job_title} ${job.description ?? ''}`.toLowerCase()
        return skillsLower.some((s) => searchText.includes(s))
      })
      setJobsCache((prev) => new Map(prev).set(h.id, matched))
    } catch {
      setJobsCache((prev) => new Map(prev).set(h.id, []))
    } finally {
      setJobsLoading((prev) => {
        const next = new Set(prev)
        next.delete(h.id)
        return next
      })
    }
  }

  return (
    <AnimatedPage>
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between"
        >
          <motion.div variants={staggerItem}>
            <h1 className="text-3xl font-bold">Dashboard</h1>
            <p className="mt-1 text-text-secondary">Track your CV analysis history and stats</p>
            {loading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="mt-3 flex items-center gap-2 text-sm text-text-muted"
              >
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
                >
                  <Loader2 className="h-4 w-4 text-primary" />
                </motion.div>
                Loading your dashboard...
              </motion.div>
            )}
          </motion.div>
          <motion.div variants={staggerItem} whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
            <Link to="/upload">
              <Button variant="gradient">
                <Sparkles className="h-4 w-4" />
                New Analysis
              </Button>
            </Link>
          </motion.div>
        </motion.div>

        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4"
        >
            {loading
            ? Array.from({ length: 4 }).map((_, i) => (
                <motion.div key={i} variants={staggerItem}>
                  <div className="animate-pulse">
                    <div className="h-8 w-16 bg-white/10 rounded mb-2"></div>
                    <div className="h-4 w-24 bg-white/5 rounded"></div>
                  </div>
                </motion.div>
              ))
            : statDefs.map((stat, i) => (
                <motion.div key={stat.label} variants={staggerItem}>
                  <ScrollReveal delay={i * 100}>
                    <Card
                      className={cn(stat.label === 'Jobs Matched' && 'cursor-pointer transition hover:border-[#ff9500]/50')}
                      onClick={stat.label === 'Jobs Matched' ? () => setShowJobs(true) : undefined}
                    >
                      <CardContent className="flex items-center gap-4 p-6">
                        <div className={cn('flex h-12 w-12 items-center justify-center rounded-xl', stat.color)}>
                          <stat.icon className="h-6 w-6" />
                        </div>
                        <div>
                          <CountUp value={stat.value} />
                          <p className="text-sm text-text-secondary">{stat.label}</p>
                        </div>
                      </CardContent>
                    </Card>
                  </ScrollReveal>
                </motion.div>
              ))}
        </motion.div>

        {history.length >= 2 && (
          <ScrollReveal>
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <LineChart className="h-5 w-5 text-primary" />
                  ATS Score Trend
                </CardTitle>
                <CardDescription>How your CV score has changed over time</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <Line
                    data={{
                      labels: [...history].reverse().map((h) =>
                        new Date(h.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
                      ),
                      datasets: [{
                        label: 'ATS Score',
                        data: [...history].reverse().map((h) => h.ats_score ?? 0),
                        borderColor: '#007aff',
                        backgroundColor: 'rgba(0, 122, 255, 0.1)',
                        fill: true,
                        tension: 0.4,
                        pointRadius: 4,
                        pointBackgroundColor: '#007aff',
                      }],
                    }}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      scales: {
                        x: { ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148, 163, 184, 0.15)' } },
                        y: { min: 0, max: 100, ticks: { color: '#94a3b8' }, grid: { color: 'rgba(148, 163, 184, 0.15)' } },
                      },
                      plugins: {
                        tooltip: {
                          backgroundColor: '#0f172a',
                          borderColor: '#334155',
                          borderWidth: 1,
                          titleColor: '#f8fafc',
                          bodyColor: '#94a3b8',
                          callbacks: {
                            label: (ctx) => `Score: ${ctx.parsed.y}/100`,
                          },
                        },
                      },
                    }}
                  />
                </div>
              </CardContent>
            </Card>
          </ScrollReveal>
        )}

        <ScrollReveal>
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Analysis History</CardTitle>
              <CardDescription>Your recent CV analyses</CardDescription>
            </CardHeader>
            <CardContent>
              {!loading && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="relative mb-6"
                >
                  <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-text-muted" />
                  <input
                    type="text"
                    placeholder="Search by filename..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="w-full rounded-lg border border-border bg-surface-light py-2.5 pl-10 pr-4 text-sm text-text-primary placeholder-text-muted transition-all focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                  />
                </motion.div>
              )}

              {loading ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.1 }}
                    >
                      <div className="h-16 rounded-lg bg-white/5 animate-pulse"></div>
                    </motion.div>
                  ))}
                </div>
              ) : filtered.length === 0 ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="py-12 text-center"
                >
                  <FileText className="mx-auto mb-3 h-10 w-10 text-text-muted" />
                  <p className="text-text-secondary">No analyses found</p>
                  <Link to="/upload">
                    <Button variant="link" className="mt-2">
                      Analyze your first CV
                    </Button>
                  </Link>
                </motion.div>
              ) : (
                <motion.div
                  variants={staggerList}
                  initial="hidden"
                  animate="visible"
                  className="space-y-3"
                >
                  <AnimatePresence>
                    {filtered.map((item) => (
                      <motion.div
                        key={item.id}
                        variants={staggerListItem}
                        layout
                        exit={{ opacity: 0, x: -20 }}
                        whileHover={{ scale: 1.01, x: 4 }}
                        whileTap={{ scale: 0.99 }}
                        onClick={() => navigate('/analysis', { state: {} })}
                        className="group flex cursor-pointer items-center gap-4 rounded-xl border border-border bg-surface-light/50 p-4 transition-all hover:border-primary/30 hover:bg-surface-light"
                      >
                        <motion.div
                          className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary-muted group-hover:bg-primary/20"
                          whileHover={{ rotate: [0, -10, 10, 0] }}
                        >
                          <FileText className="h-5 w-5 text-primary" />
                        </motion.div>
                        <div className="min-w-0 flex-1">
                          <p className="truncate font-medium">{item.filename}</p>
                          <p className="text-sm text-text-muted">
                            {new Date(item.created_at).toLocaleDateString('en-US', {
                              month: 'short',
                              day: 'numeric',
                              year: 'numeric',
                            })}
                          </p>
                        </div>
                        <div className="hidden items-center gap-3 sm:flex">
                          <motion.div className="flex -space-x-1" variants={staggerContainer}>
                            {item.skills_extracted.slice(0, 3).map((s) => (
                              <motion.div key={s} variants={staggerItem}>
                                <Badge key={s} variant="outline" className="px-2 py-0.5 text-xs">
                                  {s}
                                </Badge>
                              </motion.div>
                            ))}
                            {item.skills_extracted.length > 3 && (
                              <Badge variant="outline" className="px-2 py-0.5 text-xs">
                                +{item.skills_extracted.length - 3}
                              </Badge>
                            )}
                          </motion.div>
                        </div>
                        {item.ats_score !== null && (
                          <motion.div
                            whileHover={{ scale: 1.1 }}
                          >
                            <Badge
                              variant={item.ats_score >= 80 ? 'success' : item.ats_score >= 60 ? 'warning' : 'error'}
                              className="text-sm px-3 py-1"
                            >
                              {item.ats_score}
                            </Badge>
                          </motion.div>
                        )}
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </motion.div>
              )}
            </CardContent>
          </Card>
        </ScrollReveal>
      </div>

      <AnimatePresence>
        {showJobs && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/60 px-4 pt-10 pb-10"
            onClick={() => { setShowJobs(false); setExpandedId(null) }}
          >
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="w-full max-w-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <Card>
                <CardHeader className="flex flex-row items-center justify-between gap-4">
                  <div className="flex items-center gap-2">
                    <Briefcase className="h-5 w-5 text-[#ff9500]" />
                    <CardTitle className="text-lg">Job Matches Breakdown</CardTitle>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => { setShowJobs(false); setExpandedId(null) }}>
                    <X className="h-4 w-4" />
                  </Button>
                </CardHeader>
                <CardContent className="max-h-[60vh] overflow-y-auto space-y-2">
                  {history
                    .filter((h) => (h.job_matches ?? 0) > 0)
                    .map((h) => (
                      <div key={h.id}>
                        <button
                          onClick={() => handleRowClick(h)}
                          className="w-full flex items-center gap-4 rounded-lg border border-border bg-surface-light/50 p-4 text-left transition hover:border-primary/30 hover:bg-surface-light"
                        >
                          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#ff9500]/10 shrink-0">
                            <Briefcase className="h-5 w-5 text-[#ff9500]" />
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="truncate text-sm font-medium">{h.filename}</p>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {h.skills_extracted.slice(0, 4).map((s) => (
                                <Badge key={s} variant="outline" className="px-1.5 py-0 text-[10px]">
                                  {s}
                                </Badge>
                              ))}
                            </div>
                          </div>
                          <div className="flex flex-col items-end shrink-0">
                            <span className="text-lg font-bold text-[#ff9500]">{h.job_matches}</span>
                            <span className="text-[10px] text-text-muted">matches</span>
                          </div>
                          <div className="shrink-0 text-text-muted">
                            {expandedId === h.id ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                          </div>
                        </button>
                        <AnimatePresence>
                          {expandedId === h.id && (
                            <motion.div
                              initial={{ height: 0, opacity: 0 }}
                              animate={{ height: 'auto', opacity: 1 }}
                              exit={{ height: 0, opacity: 0 }}
                              transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
                              className="overflow-hidden"
                            >
                              <div className="pl-14 pr-4 pt-2 pb-3 space-y-2">
                                {(() => {
                                  const persisted = h.matched_jobs
                                  if (persisted && persisted.length > 0) {
                                    return <PersistedJobs jobs={persisted} skills={h.skills_extracted} />
                                  }
                                  if (jobsLoading.has(h.id)) {
                                    return (
                                      <div className="flex items-center gap-2 py-4 text-sm text-text-muted">
                                        <Loader2 className="h-4 w-4 animate-spin" />
                                        Loading matching jobs...
                                      </div>
                                    )
                                  }
                                  const cached = jobsCache.get(h.id)
                                  if (cached && cached.length > 0) {
                                    return <PersistedJobs jobs={cached.map((j) => ({ job_title: j.job_title, job_link: j.job_link, platform: j.platform, published_date: j.published_date }))} skills={h.skills_extracted} />
                                  }
                                  if (cached) {
                                    return (
                                      <div className="py-4 text-center space-y-2">
                                        <p className="text-sm text-text-muted">No matching jobs found in database</p>
                                      </div>
                                    )
                                  }
                                  return null
                                })()}
                              </div>
                            </motion.div>
                          )}
                        </AnimatePresence>
                      </div>
                    ))}
                  {history.filter((h) => (h.job_matches ?? 0) > 0).length === 0 && (
                    <p className="py-8 text-center text-sm text-text-muted">No job matches yet</p>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </AnimatedPage>
  )
}
