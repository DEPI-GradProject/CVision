import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowRight,
  BarChart3,
  Briefcase,
  FileText,
  TrendingUp,
  Clock,
  Sparkles,
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { api } from '@/api/client'
import type { AnalysisHistory, DashboardStats } from '@/types'

function StatsCard({
  value,
  label,
  sub,
  color,
  icon: Icon,
}: {
  value: string
  label: string
  sub: string
  color: 'blue' | 'orange' | 'green' | 'purple'
  icon: typeof BarChart3
}) {
  const colors = {
    blue: 'text-primary',
    orange: 'text-warning',
    green: 'text-success',
    purple: 'text-purple-500',
  }

  return (
    <Card className="flex-1 min-w-[160px]">
      <CardContent className="p-5">
        <div className="flex items-start justify-between mb-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-surface-light">
            <Icon className={cn('h-5 w-5', colors[color])} />
          </div>
          <span className="rounded-full bg-surface-light px-2.5 py-0.5 text-[10px] text-text-muted font-medium">
            {sub}
          </span>
        </div>
        <p className={cn('text-2xl font-bold', colors[color])}>{value}</p>
        <p className="text-xs text-text-secondary mt-0.5">{label}</p>
      </CardContent>
    </Card>
  )
}

export function HomePage() {
  const [history, setHistory] = useState<AnalysisHistory[]>([])
  const [stats, setStats] = useState<DashboardStats | null>(null)

  useEffect(() => {
    api.getHistory(5)
      .then((r) => setHistory(r.data))
      .catch(() => {})
    api.getStats()
      .then((r) => setStats(r.data))
      .catch(() => {})
  }, [])

  const statCards = [
    { value: String(stats?.total_analyses ?? '—'), label: 'CVs Analyzed', sub: 'All time', color: 'blue' as const, icon: FileText },
    { value: String(stats?.average_score ?? '—'), label: 'Average Score', sub: '+3 this month', color: 'orange' as const, icon: TrendingUp },
    { value: String(stats?.total_job_matches ?? '—'), label: 'Jobs Matched', sub: 'Across platforms', color: 'green' as const, icon: Briefcase },
    { value: stats?.last_analysis ?? '—', label: 'Last Analysis', sub: 'Recent', color: 'purple' as const, icon: Clock },
  ]

  return (
    <div className="space-y-6">
      {/* Hero Card */}
      <Card className="overflow-hidden border-0 bg-gradient-to-br from-[#1D4ED8] via-[#3B82F6] to-[#60A5FA]">
        <CardContent className="relative p-6 sm:p-8">
          <div className="flex flex-col gap-6 sm:flex-row sm:items-center sm:justify-between">
            <div className="max-w-xl space-y-4">
              <Badge className="w-fit rounded-full bg-white/20 text-white border-0 text-[10px] font-semibold tracking-wider px-3 py-1">
                <Sparkles className="mr-1 h-3 w-3" />
                AI-POWERED CV ANALYSIS
              </Badge>
              <h1 className="text-3xl font-bold leading-tight text-white sm:text-4xl lg:text-5xl">
                Transform Your CV
                <br />
                Career Opportunities
              </h1>
              <p className="text-sm leading-relaxed text-white/70 sm:text-base max-w-lg">
                Upload your CV and let AI analyze, score, and match it against thousands of jobs — instantly.
              </p>
              <div className="flex flex-wrap gap-3">
                <Link to="/upload">
                  <Button className="rounded-full bg-white text-primary hover:bg-white/90 shadow-lg text-sm h-11 px-6">
                    Analyze Your CV
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </Link>
                <Link to="/dashboard">
                  <Button className="rounded-full border-2 border-white/30 bg-transparent text-white hover:bg-white/10 text-sm h-11 px-6">
                    View Dashboard
                  </Button>
                </Link>
              </div>
            </div>
            <div className="hidden sm:flex items-center gap-4">
              <span className="text-5xl opacity-80">📄</span>
              <span className="text-6xl opacity-90 -mt-6">🤖</span>
              <span className="text-5xl opacity-80 -mt-3">🎯</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats Row */}
      <div className="flex flex-wrap gap-4">
        {statCards.map((s) => (
          <StatsCard key={s.label} {...s} />
        ))}
      </div>

      {/* Two Column Layout */}
      <div className="grid gap-6 lg:grid-cols-[1fr_360px]">
        {/* Left: Recent Analyses */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-4">
            <div>
              <CardTitle>Recent Analyses</CardTitle>
              <p className="text-sm text-text-secondary">Your latest CV uploads</p>
            </div>
            <Link to="/dashboard" className="text-xs font-medium text-primary hover:underline">
              View all
            </Link>
          </CardHeader>
          <CardContent className="p-0">
            {history.length === 0 ? (
              <div className="flex flex-col items-center py-12 text-center">
                <FileText className="h-10 w-10 text-text-muted mb-3" />
                <p className="text-sm text-text-secondary">No analyses yet</p>
                <Link to="/upload">
                  <Button variant="link" className="mt-1 text-xs">
                    Analyze your first CV
                  </Button>
                </Link>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left px-5 py-3 text-xs font-medium text-text-muted">FILE</th>
                      <th className="text-left px-5 py-3 text-xs font-medium text-text-muted">DATE</th>
                      <th className="text-center px-5 py-3 text-xs font-medium text-text-muted">ATS SCORE</th>
                      <th className="text-center px-5 py-3 text-xs font-medium text-text-muted">JOBS</th>
                      <th className="text-right px-5 py-3 text-xs font-medium text-text-muted">STATUS</th>
                    </tr>
                  </thead>
                  <tbody>
                    {history.map((h) => {
                      const score = h.ats_score ?? 0
                      const statusColor = score >= 80 ? 'text-success' : score >= 60 ? 'text-warning' : 'text-error'
                      const statusBg = score >= 80 ? 'bg-success/10 text-success' : score >= 60 ? 'bg-warning/10 text-warning' : 'bg-error/10 text-error'

                      return (
                        <tr key={h.id} className="border-b border-border/50 last:border-0 hover:bg-surface-light/50 transition-colors">
                          <td className="px-5 py-3.5">
                            <div className="flex items-center gap-2.5">
                              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10">
                                <FileText className="h-4 w-4 text-primary" />
                              </div>
                              <span className="font-medium text-text-primary text-sm truncate max-w-[160px]">
                                {h.filename}
                              </span>
                            </div>
                          </td>
                          <td className="px-5 py-3.5 text-text-secondary text-xs">
                            {new Date(h.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                          </td>
                          <td className="px-5 py-3.5 text-center">
                            <span className={cn('text-sm font-semibold', statusColor)}>
                              {score}
                            </span>
                          </td>
                          <td className="px-5 py-3.5 text-center text-text-secondary text-xs">
                            {h.job_matches ?? 0}
                          </td>
                          <td className="px-5 py-3.5 text-right">
                            <span className={cn('inline-flex rounded-full px-2.5 py-0.5 text-[10px] font-medium', statusBg)}>
                              {score >= 80 ? 'Excellent' : score >= 60 ? 'Good' : 'Fair'}
                            </span>
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Right: How It Works */}
        <Card>
          <CardHeader>
            <CardTitle>How It Works</CardTitle>
            <p className="text-sm text-text-secondary">From upload to insights in seconds</p>
          </CardHeader>
          <CardContent className="space-y-5">
            {[
              { icon: '📤', title: 'Upload your CV', desc: 'PDF or DOCX format, up to 10MB' },
              { icon: '🤖', title: 'AI analyzes it', desc: 'extracts skills, scores formatting, checks ATS' },
              { icon: '🎯', title: 'Get matched', desc: 'ranked job matches from thousands of live postings' },
              { icon: '📊', title: 'Track progress', desc: 'see your score trend over multiple submissions' },
            ].map((step, i) => (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, x: -10 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.08 }}
                className="flex items-start gap-3"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-surface-light text-base">
                  {step.icon}
                </div>
                <div>
                  <p className="text-sm font-medium text-text-primary">{step.title}</p>
                  <p className="text-xs text-text-secondary leading-relaxed">{step.desc}</p>
                </div>
              </motion.div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
