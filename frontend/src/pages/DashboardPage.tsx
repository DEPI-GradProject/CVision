import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  BarChart3,
  Clock,
  FileText,
  Loader2,
  Search,
  Sparkles,
  TrendingUp,
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AnimatedPage } from '@/components/AnimatedPage'
import { ScrollReveal } from '@/components/ScrollReveal'
import { StatSkeleton, ListItemSkeleton } from '@/components/Skeleton'
import { cn } from '@/lib/utils'
import { staggerContainer, staggerItem, staggerList, staggerListItem } from '@/lib/animations'
import type { AnalysisHistory } from '@/types'

const mockHistory: AnalysisHistory[] = [
  { id: '1', filename: 'software_engineer_resume.pdf', ats_score: 85, skills_extracted: ['React', 'TypeScript', 'Python', 'AWS', 'Docker'], created_at: new Date(Date.now() - 86400000).toISOString() },
  { id: '2', filename: 'product_manager_cv.docx', ats_score: 72, skills_extracted: ['Product Strategy', 'Agile', 'SQL', 'A/B Testing', 'Roadmapping'], created_at: new Date(Date.now() - 172800000).toISOString() },
  { id: '3', filename: 'data_scientist_resume.pdf', ats_score: 91, skills_extracted: ['Python', 'TensorFlow', 'PyTorch', 'SQL', 'Statistics', 'MLOps'], created_at: new Date(Date.now() - 259200000).toISOString() },
  { id: '4', filename: 'frontend_developer_cv.docx', ats_score: 68, skills_extracted: ['JavaScript', 'TypeScript', 'React', 'CSS', 'Tailwind', 'Next.js'], created_at: new Date(Date.now() - 432000000).toISOString() },
  { id: '5', filename: 'devops_engineer_resume.pdf', ats_score: 79, skills_extracted: ['Docker', 'Kubernetes', 'AWS', 'Terraform', 'CI/CD'], created_at: new Date(Date.now() - 604800000).toISOString() },
]

const statDefs = [
  { label: 'CVs Analyzed', value: '12', icon: FileText, color: 'text-primary bg-primary-muted' },
  { label: 'Average Score', value: '79', icon: BarChart3, color: 'text-emerald-400 bg-emerald-500/10' },
  { label: 'Jobs Matched', value: '47', icon: TrendingUp, color: 'text-amber-400 bg-amber-500/10' },
  { label: 'Last Analysis', value: '2h ago', icon: Clock, color: 'text-purple-400 bg-purple-500/10' },
]

function CountUp({ value, duration = 1000 }: { value: string; duration?: number }) {
  const num = parseInt(value)
  if (isNaN(num)) {
    return <span className="text-2xl font-bold">{value}</span>
  }

  const [count, setCount] = useState(0)
  const [show, setShow] = useState(false)

  useEffect(() => {
    setShow(true)
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

export function DashboardPage() {
  const navigate = useNavigate()
  const [history] = useState<AnalysisHistory[]>(mockHistory)
  const [search, setSearch] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const t = setTimeout(() => setLoading(false), 800)
    return () => clearTimeout(t)
  }, [])

  const filtered = history.filter((h) =>
    h.filename.toLowerCase().includes(search.toLowerCase()),
  )

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
                  <StatSkeleton />
                </motion.div>
              ))
            : statDefs.map((stat, i) => (
                <motion.div key={stat.label} variants={staggerItem}>
                  <ScrollReveal delay={i * 100}>
                    <Card>
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

        <ScrollReveal>
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Analysis History</CardTitle>
              <CardDescription>Your recent CV analyses</CardDescription>
            </CardHeader>
            <CardContent>
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

              {loading ? (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.1 }}
                    >
                      <ListItemSkeleton />
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
                            {item.skills_extracted.slice(0, 3).map((s, i) => (
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
    </AnimatedPage>
  )
}
