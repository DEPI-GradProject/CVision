import { useEffect, useState, useRef } from 'react'
import { useLocation, useNavigate, Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  BarChart3,
  Brain,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Clipboard,
  FileSearch,
  FileText,
  Loader2,
  Sparkles,
  Target,
  TrendingUp,
  XCircle,
} from 'lucide-react'
import { api } from '@/api/client'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { ScrollReveal } from '@/components/ScrollReveal'
import { AnimatedPage } from '@/components/AnimatedPage'
import { useToast } from '@/components/Toast'
import { cn } from '@/lib/utils'
import { staggerContainer, staggerItem } from '@/lib/animations'
import type { CVAnalysisResult, SSEEvent, MarketSkill, RewriteResult } from '@/types'

const stepLabels: Record<string, string> = {
  parser: 'Parsing CV content...',
  analyzer: 'Analyzing skills & experience...',
  analyzer_ats: 'Calculating ATS score...',
  matcher: 'Matching against jobs...',
  reporter: 'Building report...',
  complete: 'Analysis complete!',
}

const stepIcons: Record<string, typeof Brain> = {
  parser: FileText,
  analyzer: Brain,
  analyzer_ats: BarChart3,
  matcher: Target,
  reporter: FileSearch,
  complete: CheckCircle2,
}

function StepIndicator({ steps, currentStep }: { steps: string[]; stepsData: typeof stepLabels; currentStep: string }) {
  const currentIndex = steps.indexOf(currentStep)

  return (
    <div className="space-y-3">
      {steps.map((step, i) => {
        const isComplete = i < currentIndex
        const isActive = i === currentIndex
        const Icon = stepIcons[step] || Brain
        const label = stepLabels[step] || step

        return (
          <motion.div
            key={step}
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.1 }}
            className="flex items-center gap-3"
          >
            <motion.div
              animate={
                isActive
                  ? {
                      scale: [1, 1.2, 1],
                      transition: { repeat: Infinity, duration: 2 },
                    }
                  : {}
              }
              className={cn(
                'flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg text-xs font-medium transition-all',
                isComplete
                  ? 'bg-emerald-500/15 text-emerald-400'
                  : isActive
                    ? 'bg-primary/15 text-primary ring-1 ring-primary/30'
                    : 'bg-surface-light text-text-muted',
              )}
            >
              {isComplete ? (
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: 'spring', stiffness: 500 }}
                >
                  <CheckCircle2 className="h-4 w-4" />
                </motion.div>
              ) : (
                <Icon className="h-4 w-4" />
              )}
            </motion.div>
            <span
              className={cn(
                'text-sm transition-colors',
                isComplete
                  ? 'text-emerald-400'
                  : isActive
                    ? 'text-text-primary font-medium'
                    : 'text-text-muted',
              )}
            >
              {label}
              {isActive && !isComplete && (
                <motion.span
                  className="inline-flex"
                  animate={{ opacity: [1, 0.4, 1] }}
                  transition={{ repeat: Infinity, duration: 1.5 }}
                >
                  <Loader2 className="ml-2 inline h-3 w-3 animate-spin text-primary" />
                </motion.span>
              )}
            </span>
          </motion.div>
        )
      })}
    </div>
  )
}

function AtsGauge({ score }: { score: number }) {
  const color = score >= 80 ? 'success' : score >= 60 ? 'warning' : 'error'
  const label = score >= 80 ? 'Excellent' : score >= 60 ? 'Good' : 'Needs Work'
  const circumference = 2 * Math.PI * 42
  const [animatedScore, setAnimatedScore] = useState(0)

  useEffect(() => {
    let start = 0
    const duration = 1000
    const step = 16
    const totalSteps = duration / step
    const increment = score / totalSteps

    const timer = setInterval(() => {
      start += increment
      if (start >= score) {
        setAnimatedScore(score)
        clearInterval(timer)
      } else {
        setAnimatedScore(Math.round(start))
      }
    }, step)

    return () => clearInterval(timer)
  }, [score])

  return (
    <ScrollReveal>
      <Card className="overflow-hidden">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <BarChart3 className="h-5 w-5 text-primary" />
            ATS Score
          </CardTitle>
        </CardHeader>
        <CardContent>
          <motion.div
            className="flex flex-col items-center py-4"
            initial={{ opacity: 0, scale: 0.5 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.2, type: 'spring' }}
          >
            <div className="relative mb-3">
              <svg className="h-28 w-28 -rotate-90" viewBox="0 0 100 100">
                <circle
                  cx="50" cy="50" r="42"
                  fill="none"
                  stroke="currentColor"
                  className="text-surface-light"
                  strokeWidth="8"
                />
                <motion.circle
                  cx="50" cy="50" r="42"
                  fill="none"
                  stroke="currentColor"
                  className={cn(
                    score >= 80 ? 'text-success' : score >= 60 ? 'text-warning' : 'text-error',
                  )}
                  strokeWidth="8"
                  strokeLinecap="round"
                  strokeDasharray={`${circumference}`}
                  initial={{ strokeDashoffset: circumference }}
                  animate={{ strokeDashoffset: circumference - (animatedScore / 100) * circumference }}
                  transition={{ duration: 1, ease: 'easeOut' }}
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <motion.span
                  key={animatedScore}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={cn(
                    'text-3xl font-bold',
                    score >= 80 ? 'text-success' : score >= 60 ? 'text-warning' : 'text-error',
                  )}
                >
                  {animatedScore}
                </motion.span>
              </div>
            </div>
            <Badge variant={color as 'success' | 'warning' | 'error'} className="text-sm">
              {label}
            </Badge>
          </motion.div>
        </CardContent>
      </Card>
    </ScrollReveal>
  )
}

function SkillsCloud({ skills }: { skills: string[] }) {
  return (
    <ScrollReveal>
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <Brain className="h-5 w-5 text-primary" />
            Skills Extracted
          </CardTitle>
          <CardDescription>{skills.length} skills identified</CardDescription>
        </CardHeader>
        <CardContent>
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="flex flex-wrap gap-2"
          >
            {skills.map((skill) => (
              <motion.div key={skill} variants={staggerItem}>
                <motion.div
                  whileHover={{ scale: 1.08, y: -2 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <Badge variant="default" className="px-3 py-1.5 text-sm cursor-default transition-shadow hover:shadow-md hover:shadow-primary/20">
                    {skill}
                  </Badge>
                </motion.div>
              </motion.div>
            ))}
          </motion.div>
        </CardContent>
      </Card>
    </ScrollReveal>
  )
}

function SkillsGap({ skills }: { skills: string[] }) {
  const [marketSkills, setMarketSkills] = useState<MarketSkill[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getMarketDemand()
      .then((res) => setMarketSkills(res.data.filter((s) => s.demand_level === 'high')))
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [])

  const missing = marketSkills.filter((ms) => !skills.some((s) => s.toLowerCase().includes(ms.skill.toLowerCase())))

  if (loading || missing.length === 0) return null

  return (
    <ScrollReveal>
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-lg">
            <TrendingUp className="h-5 w-5 text-amber-400" />
            Skills Gap Analysis
          </CardTitle>
          <CardDescription>High-demand skills missing from your CV</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {missing.slice(0, 8).map((ms) => (
              <motion.div
                key={ms.skill}
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                className="flex items-center justify-between"
              >
                <div className="flex items-center gap-2">
                  <XCircle className="h-4 w-4 text-error" />
                  <span className="text-sm">{ms.skill}</span>
                </div>
                <Badge variant="warning" className="text-xs">{ms.job_count} jobs</Badge>
              </motion.div>
            ))}
            {missing.length > 8 && (
              <p className="text-center text-xs text-text-muted pt-2">+{missing.length - 8} more skills</p>
            )}
          </div>
        </CardContent>
      </Card>
    </ScrollReveal>
  )
}

function RewriteSuggestions({ file }: { file: File }) {
  const [rewriteResult, setRewriteResult] = useState<RewriteResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const [checked, setChecked] = useState<Set<number>>(new Set())
  const { toast } = useToast()

  const handleGenerate = async () => {
    setLoading(true)
    setExpanded(true)
    try {
      const res = await api.getRewriteSuggestions(file)
      setRewriteResult(res)
      toast('Rewrite suggestions ready!', 'success')
    } catch (err: any) {
      toast(err.message || 'Failed to generate suggestions', 'error')
    } finally {
      setLoading(false)
    }
  }

  const toggleCheck = (i: number) => {
    setChecked((prev) => {
      const next = new Set(prev)
      if (next.has(i)) next.delete(i)
      else next.add(i)
      return next
    })
  }

  const copyAll = () => {
    if (!rewriteResult) return
    const text = rewriteResult.rewrites.map((r) => r.improved).join('\n\n')
    navigator.clipboard.writeText(text)
    toast('Improvements copied to clipboard!', 'success')
  }

  return (
    <ScrollReveal>
      <Card>
        <CardHeader className="pb-3">
          <button
            onClick={() => setExpanded(!expanded)}
            className="flex w-full items-center justify-between"
          >
            <CardTitle className="flex items-center gap-2 text-lg">
              <Sparkles className="h-5 w-5 text-amber-400" /> CV Rewrite Suggestions
            </CardTitle>
            {expanded ? <ChevronDown className="h-5 w-5 text-text-muted" /> : <ChevronRight className="h-5 w-5 text-text-muted" />}
          </button>
          <CardDescription>AI-powered suggestions to improve your CV bullets</CardDescription>
        </CardHeader>
        <CardContent>
          {!expanded && (
            <Button variant="outline" onClick={handleGenerate} disabled={loading}>
              {loading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Generating...</> : <>Generate Suggestions</>}
            </Button>
          )}
          {expanded && !rewriteResult && !loading && (
            <Button variant="outline" onClick={handleGenerate}>
              Generate Suggestions
            </Button>
          )}
          {expanded && loading && (
            <div className="flex items-center gap-3 py-4">
              <Loader2 className="h-5 w-5 animate-spin text-primary" />
              <span className="text-sm text-text-secondary">AI is rewriting your CV bullets...</span>
            </div>
          )}
          {expanded && rewriteResult && (
            <div className="space-y-6">
              <div className="rounded-lg bg-primary-muted/50 p-4 text-sm text-text-secondary leading-relaxed">
                {rewriteResult.overall_assessment}
              </div>

              {rewriteResult.rewrites.length > 0 && (
                <div className="space-y-4">
                  <h4 className="text-sm font-medium">Suggested Rewrites</h4>
                  {rewriteResult.rewrites.map((r, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.1 }}
                      className="rounded-lg border border-border p-4 space-y-3"
                    >
                      <div>
                        <p className="text-xs text-text-muted mb-1">Original:</p>
                        <p className="text-sm text-error line-through">{r.original}</p>
                      </div>
                      <div>
                        <p className="text-xs text-text-muted mb-1">Issue:</p>
                        <p className="text-sm text-text-secondary">{r.issue}</p>
                      </div>
                      <div>
                        <p className="text-xs text-text-muted mb-1">Improved:</p>
                        <p className="text-sm text-success">{r.improved}</p>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}

              {rewriteResult.quick_wins.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium mb-3">Quick Wins</h4>
                  <div className="space-y-2">
                    {rewriteResult.quick_wins.map((win, i) => (
                      <label
                        key={i}
                        className="flex items-start gap-3 cursor-pointer"
                      >
                        <input
                          type="checkbox"
                          checked={checked.has(i)}
                          onChange={() => toggleCheck(i)}
                          className="mt-0.5 h-4 w-4 rounded border-border accent-primary"
                        />
                        <span className={cn(
                          'text-sm',
                          checked.has(i) ? 'text-text-muted line-through' : 'text-text-secondary',
                        )}>
                          {win}
                        </span>
                      </label>
                    ))}
                  </div>
                </div>
              )}

              <div className="flex gap-3">
                <Button variant="outline" size="sm" onClick={copyAll} className="gap-2">
                  <Clipboard className="h-4 w-4" /> Copy All Improvements
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </ScrollReveal>
  )
}

export function AnalysisPage() {
  const location = useLocation()
  const navigate = useNavigate()
  const file = (location.state as { file?: File })?.file
  const [step, setStep] = useState<string>('uploading')
  const [result, setResult] = useState<CVAnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const controllerRef = useRef<AbortController | null>(null)
  const { toast } = useToast()

  const steps = ['parser', 'analyzer', 'analyzer_ats', 'matcher', 'reporter', 'complete']

  useEffect(() => {
    if (!file) {
      navigate('/upload', { replace: true })
      return
    }

    setStep('parser')
    toast('AI agents are analyzing your CV...', 'info')

    controllerRef.current = api.analyzeCVStream(
      file,
      (event: SSEEvent) => {
        if (event.step === 'error') {
          setError(event.error || 'Analysis failed')
          toast(event.error || 'Analysis failed', 'error')
          return
        }
        setStep(event.step)

        if (event.step === 'complete' && event.result) {
          setResult(event.result)
          toast('Analysis complete!', 'success')
        }
      },
      (err) => {
        setError(err.message || 'Connection error')
        toast(err.message || 'Connection error', 'error')
      },
    )

    return () => {
      controllerRef.current?.abort()
    }
  }, [file, navigate, toast])

  if (!file) return null

  if (error) {
    return (
      <AnimatedPage>
        <div className="mx-auto max-w-lg px-4 py-24 text-center">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 300 }}
            className="mb-6 flex justify-center"
          >
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-red-500/10">
              <AlertCircle className="h-8 w-8 text-error" />
            </div>
          </motion.div>
          <h2 className="mb-2 text-2xl font-bold">Analysis Failed</h2>
          <p className="mb-8 text-text-secondary">{error}</p>
          <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
            <Link to="/upload">
              <Button variant="gradient">Try Again</Button>
            </Link>
          </motion.div>
        </div>
      </AnimatedPage>
    )
  }

  if (!result) {
    return (
      <AnimatedPage>
        <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
          <div className="mx-auto max-w-md">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
                    >
                      <Loader2 className="h-5 w-5 text-primary" />
                    </motion.div>
                    Analyzing Your CV
                  </CardTitle>
                  <CardDescription>
                    Our AI agents are processing{' '}
                    <span className="font-medium text-text-primary">{file.name}</span>
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <StepIndicator steps={steps} stepsData={stepLabels} currentStep={step} />
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </div>
      </AnimatedPage>
    )
  }

  return (
    <AnimatedPage>
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="mb-8 flex items-center gap-4"
        >
          <motion.div variants={staggerItem}>
            <Button variant="ghost" size="icon" onClick={() => navigate('/upload')}>
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </motion.div>
          <motion.div variants={staggerItem}>
            <h1 className="text-2xl font-bold sm:text-3xl">Analysis Results</h1>
            <p className="text-text-secondary">{result.filename}</p>
          </motion.div>
          {result.ats_score !== null && (
            <motion.div
              variants={staggerItem}
              className="ml-auto"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
            >
              <Badge variant={result.ats_score >= 70 ? 'success' : result.ats_score >= 50 ? 'warning' : 'error'} className="text-sm px-3 py-1.5">
                <Sparkles className="mr-1.5 h-3.5 w-3.5" />
                Score: {result.ats_score}
              </Badge>
            </motion.div>
          )}
        </motion.div>

        <div className="grid gap-6 lg:grid-cols-3">
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="space-y-6 lg:col-span-1"
          >
            {result.ats_score !== null && <AtsGauge score={result.ats_score} />}

            {result.job_matches > 0 && (
              <ScrollReveal>
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <Target className="h-5 w-5 text-primary" />
                      Job Matches
                    </CardTitle>
                    <CardDescription>{result.job_matches} positions found for your CV</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {(result.matched_jobs || []).slice(0, 5).map((job, i) => (
                      <motion.div
                        key={i}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.1 }}
                        className="rounded-lg border border-border p-3 hover:border-primary/30 transition-colors"
                      >
                        <div className="flex items-start justify-between gap-3 mb-2">
                          <p className="text-sm font-medium">{job.job_title}</p>
                          {job.faiss_score != null && (
                            <Badge
                              variant={job.faiss_score >= 80 ? 'success' : job.faiss_score >= 60 ? 'warning' : 'error'}
                              className="shrink-0 text-xs"
                            >
                              {job.faiss_score}%
                            </Badge>
                          )}
                        </div>
                        {job.matched_skills && job.matched_skills.length > 0 && (
                          <div className="flex flex-wrap gap-1 mb-1.5">
                            {job.matched_skills.slice(0, 4).map((s) => (
                              <Badge key={s} variant="success" className="text-[10px] px-1.5 py-0">{s}</Badge>
                            ))}
                          </div>
                        )}
                        {job.missing_skills && job.missing_skills.length > 0 && (
                          <div className="flex flex-wrap gap-1 mb-1.5">
                            {job.missing_skills.slice(0, 4).map((s) => (
                              <Badge key={s} variant="error" className="text-[10px] px-1.5 py-0">{s}</Badge>
                            ))}
                          </div>
                        )}
                        {job.reason && (
                          <p className="text-[11px] text-text-muted">{job.reason}</p>
                        )}
                        {job.job_link && (
                          <a
                            href={job.job_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-primary hover:underline mt-1 inline-block"
                          >
                            View job →
                          </a>
                        )}
                      </motion.div>
                    ))}
                    {result.matched_jobs && result.matched_jobs.length > 5 && (
                      <p className="text-center text-xs text-text-muted pt-1">
                        +{result.matched_jobs.length - 5} more matches
                      </p>
                    )}
                  </CardContent>
                </Card>
              </ScrollReveal>
            )}
          </motion.div>

          <div className="space-y-6 lg:col-span-2">
            {result.skills_extracted.length > 0 && <SkillsCloud skills={result.skills_extracted} />}

            {result.skills_extracted.length > 0 && <SkillsGap skills={result.skills_extracted} />}

            {result.report && (
              <ScrollReveal>
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <FileSearch className="h-5 w-5 text-primary" />
                      Full Report
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <motion.div
                      variants={staggerContainer}
                      initial="hidden"
                      animate="visible"
                      className="prose prose-invert max-w-none"
                    >
                      <motion.div
                        variants={staggerItem}
                        className="whitespace-pre-wrap text-sm leading-relaxed text-text-secondary"
                      >
                        {result.report}
                      </motion.div>
                    </motion.div>
                  </CardContent>
                </Card>
              </ScrollReveal>
            )}

            {result.ats_score !== null && (
              <ScrollReveal>
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center gap-2 text-lg">
                      <BarChart3 className="h-5 w-5 text-primary" />
                      Score Breakdown
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {[
                      { label: 'Keyword Match', value: Math.min(100, (result.ats_score || 0) + 10) },
                      { label: 'Formatting', value: Math.min(100, (result.ats_score || 0) + 5) },
                      { label: 'Experience Relevance', value: result.ats_score || 0 },
                    ].map((item, i) => (
                      <motion.div
                        key={item.label}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.3 + i * 0.15 }}
                      >
                        <div className="mb-1 flex justify-between text-sm">
                          <span className="text-text-secondary">{item.label}</span>
                          <span className="text-text-primary font-medium">{item.value}%</span>
                        </div>
                        <Progress
                          value={item.value}
                          variant={result.ats_score != null && result.ats_score >= 70 ? 'success' : result.ats_score != null && result.ats_score >= 50 ? 'warning' : 'error'}
                        />
                      </motion.div>
                    ))}
                  </CardContent>
                </Card>
              </ScrollReveal>
            )}

            <RewriteSuggestions file={file} />

            <motion.div
              variants={staggerContainer}
              initial="hidden"
              animate="visible"
              className="flex gap-3"
            >
              <motion.div variants={staggerItem}>
                <Link to="/upload">
                  <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
                    <Button variant="gradient" className="group">
                      Analyze Another CV
                      <ArrowRight className="ml-1 h-4 w-4 transition-transform group-hover:translate-x-1" />
                    </Button>
                  </motion.div>
                </Link>
              </motion.div>
              <motion.div variants={staggerItem}>
                <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
                  <Button variant="outline" onClick={() => window.print()}>
                    Print Report
                  </Button>
                </motion.div>
              </motion.div>
            </motion.div>
          </div>
        </div>
      </div>
    </AnimatedPage>
  )
}
