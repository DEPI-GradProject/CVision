import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Briefcase, RefreshCw, AlertCircle, CheckCircle2, XCircle, Lightbulb, Loader2, FileText, Search, BarChart3, ChevronDown, FileEdit, Sparkles, PenLine, X, Copy, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { AnimatedPage } from '@/components/AnimatedPage'
import { cn } from '@/lib/utils'
import { staggerContainer, staggerItem } from '@/lib/animations'
import { api } from '@/api/client'
import type { CoverLetterResult, JobMatchResult, StandOutResult, TailorResumeResult } from '@/types'

const loadingSteps = [
  { icon: FileText, label: 'Parsing CV...' },
  { icon: Search, label: 'Analyzing job...' },
  { icon: BarChart3, label: 'Calculating match...' },
]

const featureLabels: Record<string, { title: string; icon: typeof FileEdit }> = {
  tailor: { title: 'Tailored Resume', icon: PenLine },
  standout: { title: 'Ways to Stand Out', icon: Sparkles },
  cover: { title: 'Cover Letter', icon: FileEdit },
}

export function JobMatchPage() {
  const [cvFile, setCvFile] = useState<File | null>(null)
  const [cvText, setCvText] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [result, setResult] = useState<JobMatchResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [loadingStep, setLoadingStep] = useState(0)
  const [error, setError] = useState<string | null>(null)

  const [activeFeature, setActiveFeature] = useState<string | null>(null)
  const [featureLoading, setFeatureLoading] = useState(false)
  const [featureResult, setFeatureResult] = useState<TailorResumeResult | StandOutResult | CoverLetterResult | null>(null)
  const [featureError, setFeatureError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f) return
    setCvFile(f)
  }

  const handleMatch = async () => {
    if (!jobDescription.trim()) return
    if (!cvFile && !cvText.trim()) return
    setLoading(true)
    setError(null)
    setResult(null)
    setLoadingStep(0)
    const stepTimer = setInterval(() => {
      setLoadingStep((s) => Math.min(s + 1, loadingSteps.length - 1))
    }, 3000)
    try {
      let res
      if (cvFile) {
        res = await api.matchJobFile(cvFile, jobDescription)
      } else {
        res = await api.matchJob(jobDescription, cvText)
      }
      setResult(res)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to match job')
    } finally {
      clearInterval(stepTimer)
      setLoading(false)
    }
  }

  const handleReset = () => {
    setResult(null)
    setError(null)
    setCvText('')
    setJobDescription('')
    setCvFile(null)
  }

  const handleFeature = async (feature: string) => {
    const text = result?.cv_text || ''
    if (!text || !jobDescription.trim()) return
    setActiveFeature(feature)
    setFeatureLoading(true)
    setFeatureError(null)
    setFeatureResult(null)
    setCopied(false)
    try {
      let res
      if (feature === 'tailor') {
        res = await api.tailorResume(jobDescription, text)
      } else if (feature === 'standout') {
        res = await api.standOut(jobDescription, text)
      } else {
        res = await api.coverLetter(jobDescription, text)
      }
      setFeatureResult(res)
    } catch (err: unknown) {
      setFeatureError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setFeatureLoading(false)
    }
  }

  const handleCopy = async () => {
    const text = featureResult
      ? 'tailored_resume' in featureResult
        ? featureResult.tailored_resume
        : 'cover_letter' in featureResult
          ? featureResult.cover_letter
          : JSON.stringify(featureResult, null, 2)
      : ''
    try {
      await navigator.clipboard.writeText(text)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch { /* clipboard may be denied */ }
  }

  const closeModal = () => {
    setActiveFeature(null)
    setFeatureResult(null)
    setFeatureError(null)
    setFeatureLoading(false)
  }

  const renderFeatureContent = () => {
    if (featureLoading) {
      return (
        <div className="flex flex-col items-center gap-3 py-12">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
          <p className="text-sm text-text-muted">Generating...</p>
        </div>
      )
    }
    if (featureError) {
      return (
        <div className="flex items-center gap-2 rounded-lg bg-red-500/10 px-4 py-3 text-sm text-error">
          <AlertCircle className="h-4 w-4" /> {featureError}
        </div>
      )
    }
    if (!featureResult) return null

    if ('tailored_resume' in featureResult) {
      return (
        <div className="space-y-4">
          <div className="rounded-lg border border-border bg-surface-light p-4">
            <pre className="whitespace-pre-wrap text-sm leading-relaxed font-sans text-text-primary">
              {featureResult.tailored_resume}
            </pre>
          </div>
        </div>
      )
    }

    if ('cover_letter' in featureResult) {
      return (
        <div className="space-y-4">
          <div className="rounded-lg border border-border bg-surface-light p-4">
            <pre className="whitespace-pre-wrap text-sm leading-relaxed font-sans text-text-primary">
              {featureResult.cover_letter}
            </pre>
          </div>
        </div>
      )
    }

    if ('unique_selling_points' in featureResult) {
      return (
        <div className="space-y-5">
          <div>
            <h4 className="text-sm font-semibold mb-2 text-primary">Unique Selling Points</h4>
            <ul className="space-y-1.5">
              {featureResult.unique_selling_points.map((p, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-text-secondary">
                  <Sparkles className="mt-0.5 h-4 w-4 flex-shrink-0 text-[#ff9500]" />
                  <span>{p}</span>
                </li>
              ))}
            </ul>
          </div>
          {featureResult.suggested_certifications.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold mb-2 text-primary">Suggested Certifications</h4>
              <div className="flex flex-wrap gap-2">
                {featureResult.suggested_certifications.map((c, i) => (
                  <Badge key={i} variant="default">{c}</Badge>
                ))}
              </div>
            </div>
          )}
          {featureResult.project_ideas.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold mb-2 text-primary">Project Ideas</h4>
              <ul className="space-y-1.5">
                {featureResult.project_ideas.map((p, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-text-secondary">
                    <Lightbulb className="mt-0.5 h-4 w-4 flex-shrink-0 text-primary" />
                    <span>{p}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {featureResult.skill_enhancements.length > 0 && (
            <div>
              <h4 className="text-sm font-semibold mb-2 text-primary">Skill Enhancements</h4>
              <div className="flex flex-wrap gap-2">
                {featureResult.skill_enhancements.map((s, i) => (
                  <Badge key={i} variant="outline">{s}</Badge>
                ))}
              </div>
            </div>
          )}
          <div className="rounded-lg bg-primary/5 p-4">
            <h4 className="text-sm font-semibold mb-1 text-primary">Strategy</h4>
            <p className="text-sm text-text-secondary">{featureResult.overall_strategy}</p>
          </div>
        </div>
      )
    }

    return null
  }

  return (
    <AnimatedPage>
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <motion.div variants={staggerContainer} initial="hidden" animate="visible" className="mx-auto max-w-3xl text-center">
          <motion.div variants={staggerItem}>
            <h1 className="text-3xl font-bold sm:text-4xl">Job Match</h1>
          </motion.div>
          <motion.div variants={staggerItem}>
            <p className="mt-3 text-text-secondary">
              Paste a job description and see how well your CV matches
            </p>
          </motion.div>
        </motion.div>

        {!result && (
        <div className="mx-auto mt-12 grid max-w-5xl gap-8 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Your CV</CardTitle>
              <CardDescription>Upload or paste your CV text</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Upload CV (PDF/DOCX)</label>
                <input
                  type="file"
                  accept=".pdf,.docx"
                  onChange={handleFileChange}
                  className="w-full rounded-lg border border-border bg-surface-light px-3 py-2 text-sm file:mr-3 file:rounded file:border-0 file:bg-primary file:px-3 file:py-1 file:text-sm file:text-white"
                />
                {cvFile && (
                  <p className="mt-1 text-xs text-text-muted">Using: {cvFile.name}</p>
                )}
              </div>
              <div>
                <label className="block text-sm font-medium mb-2">Or paste CV text</label>
                <textarea
                  value={cvText}
                  onChange={(e) => setCvText(e.target.value)}
                  placeholder="Paste your CV text here..."
                  rows={8}
                  className="w-full rounded-lg border border-border bg-surface-light px-3 py-2 text-sm placeholder-text-muted focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Job Description</CardTitle>
              <CardDescription>Paste the job description you want to match against</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste job description here..."
                rows={10}
                className="w-full rounded-lg border border-border bg-surface-light px-3 py-2 text-sm placeholder-text-muted focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <Button
                variant="gradient"
                className="w-full"
                disabled={(!cvFile && !cvText.trim()) || !jobDescription.trim() || loading}
                onClick={handleMatch}
              >
                {loading ? (
                  <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Matching...</>
                ) : (
                  <><Briefcase className="mr-2 h-4 w-4" /> Match Job</>
                )}
              </Button>
            </CardContent>
          </Card>
        </div>
        )}

        {loading && !result && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mx-auto mt-8 max-w-md"
          >
            <Card>
              <CardContent className="p-6 space-y-4">
                {loadingSteps.map((step, i) => (
                  <div key={step.label} className="flex items-center gap-3">
                    <step.icon className={cn(
                      'h-5 w-5',
                      i <= loadingStep ? 'text-primary animate-pulse' : 'text-text-muted',
                    )} />
                    <span className={cn(
                      'text-sm',
                      i <= loadingStep ? 'text-text-primary font-medium' : 'text-text-muted',
                    )}>
                      {step.label}
                    </span>
                    {i < loadingStep && <CheckCircle2 className="ml-auto h-4 w-4 text-success" />}
                  </div>
                ))}
              </CardContent>
            </Card>
          </motion.div>
        )}

        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mx-auto mt-6 max-w-2xl flex items-center gap-2 rounded-lg bg-red-500/10 px-4 py-3 text-sm text-error"
          >
            <AlertCircle className="h-4 w-4" /> {error}
          </motion.div>
        )}

        <AnimatePresence>
          {result && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mx-auto mt-12 max-w-3xl space-y-6"
            >
              <Card className="overflow-hidden">
                <CardContent className="p-0">
                  <div className="flex flex-col items-center gap-3 p-8 pb-6">
                    <div className="relative flex h-24 w-24 items-center justify-center">
                      <svg className="h-24 w-24 -rotate-90" viewBox="0 0 100 100">
                        <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="8" className="text-border" />
                        <circle
                          cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="8"
                          strokeDasharray={`${result.match_score * 2.827} 282.7`}
                          className={cn(
                            'transition-all duration-1000',
                            result.match_score >= 75 ? 'text-success' : result.match_score >= 50 ? 'text-[#ff9500]' : 'text-error',
                          )}
                          strokeLinecap="round"
                        />
                      </svg>
                      <span className={cn(
                        'absolute text-3xl font-bold',
                        result.match_score >= 75 ? 'text-success' : result.match_score >= 50 ? 'text-[#ff9500]' : 'text-error',
                      )}>
                        {result.match_score}%
                      </span>
                    </div>
                    <Badge
                      variant={result.match_score >= 75 ? 'success' : result.match_score >= 50 ? 'warning' : 'error'}
                      className="text-sm px-3 py-1"
                    >
                      {result.match_score >= 75 ? 'High Match' : result.match_score >= 50 ? 'Medium Match' : 'Low Match'}
                    </Badge>
                  </div>
                  <div className={cn(
                    'px-8 py-5 border-t border-border',
                    result.match_score >= 75
                      ? 'bg-success/5'
                      : result.match_score >= 50
                        ? 'bg-[#ff9500]/5'
                        : 'bg-error/5',
                  )}>
                    <p className="font-semibold text-sm mb-1">
                      {result.match_score >= 75
                        ? 'Job match is high, we can help you stand out'
                        : result.match_score >= 50
                          ? 'Decent match, we can help improve your chances'
                          : 'Low match, here\u2019s how to bridge the gap'}
                    </p>
                    <p className="text-sm text-text-muted">
                      {result.match_score >= 75
                        ? 'Your profile and resume match the required qualifications well.'
                        : result.match_score >= 50
                          ? 'You have some relevant skills, but a few key areas need attention.'
                          : 'Your profile needs significant improvement to match this role.'}
                    </p>
                  </div>
                  <div className="grid grid-cols-2 divide-x divide-border border-t border-border">
                    <button
                      onClick={() => document.getElementById('match-details')?.scrollIntoView({ behavior: 'smooth' })}
                      className="flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-surface-light/50 transition-colors"
                    >
                      <ChevronDown className="h-4 w-4" /> Show match details
                    </button>
                    <button
                      onClick={() => handleFeature('tailor')}
                      disabled={featureLoading && activeFeature === 'tailor'}
                      className="flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-surface-light/50 transition-colors disabled:opacity-50"
                    >
                      <PenLine className="h-4 w-4" /> Tailor my resume
                    </button>
                  </div>
                  <div className="grid grid-cols-2 divide-x divide-border border-t border-border">
                    <button
                      onClick={() => handleFeature('standout')}
                      disabled={featureLoading && activeFeature === 'standout'}
                      className="flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-surface-light/50 transition-colors disabled:opacity-50"
                    >
                      <Sparkles className="h-4 w-4" /> Help me stand out
                    </button>
                    <button
                      onClick={() => handleFeature('cover')}
                      disabled={featureLoading && activeFeature === 'cover'}
                      className="flex items-center justify-center gap-2 px-4 py-3 text-sm font-medium text-text-secondary hover:text-text-primary hover:bg-surface-light/50 transition-colors disabled:opacity-50"
                    >
                      <FileEdit className="h-4 w-4" /> Create cover letter
                    </button>
                  </div>
                  <div className="border-t border-border px-8 py-2.5 text-center">
                    <span className="text-[11px] text-text-muted">
                      BETA &bull; Is this information helpful?
                    </span>
                  </div>
                </CardContent>
              </Card>

              <Card id="match-details">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-primary" /> Keyword Coverage
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-4">
                    <Progress
                      value={result.keyword_coverage * 100}
                      variant={result.keyword_coverage >= 0.7 ? 'success' : result.keyword_coverage >= 0.4 ? 'warning' : 'error'}
                      className="flex-1"
                    />
                    <span className={cn(
                      'text-sm font-medium whitespace-nowrap',
                      result.keyword_coverage >= 0.7 ? 'text-success' : result.keyword_coverage >= 0.4 ? 'text-[#ff9500]' : 'text-error',
                    )}>
                      {Math.round(result.keyword_coverage * 100)}%
                    </span>
                  </div>
                </CardContent>
              </Card>

              <div className="grid gap-6 sm:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-success">
                      <CheckCircle2 className="h-5 w-5" /> Matched Skills
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {result.matched_skills.length === 0 ? (
                      <p className="text-sm text-text-muted">No matching skills found</p>
                    ) : (
                      <div className="flex flex-wrap gap-2">
                        {result.matched_skills.map((s) => (
                          <Badge key={s} variant="success">{s}</Badge>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-error">
                      <XCircle className="h-5 w-5" /> Missing Skills
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {result.missing_skills.length === 0 ? (
                      <p className="text-sm text-text-muted">No missing skills</p>
                    ) : (
                      <div className="flex flex-wrap gap-2">
                        {result.missing_skills.map((s) => (
                          <Badge key={s} variant="error">{s}</Badge>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-primary">
                    <Lightbulb className="h-5 w-5" /> Improvement Tips
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ol className="space-y-3">
                    {result.improvement_tips.map((tip, i) => (
                      <motion.li
                        key={i}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: i * 0.15 }}
                        className="flex items-start gap-3"
                      >
                        <span className="mt-0.5 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-primary-muted text-xs font-medium text-primary">
                          {i + 1}
                        </span>
                        <span className="text-text-secondary">{tip}</span>
                      </motion.li>
                    ))}
                  </ol>
                </CardContent>
              </Card>

              <div className="flex justify-center">
                <Button variant="outline" onClick={handleReset} className="gap-2">
                  <RefreshCw className="h-4 w-4" /> Try Another Job
                </Button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Feature Result Modal */}
      <AnimatePresence>
        {activeFeature && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/60 px-4 pt-10 pb-10"
            onClick={closeModal}
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
                    {(() => {
                      const Icon = featureLabels[activeFeature]?.icon || FileEdit
                      return <Icon className="h-5 w-5 text-primary" />
                    })()}
                    <CardTitle className="text-lg">{featureLabels[activeFeature]?.title || 'Feature'}</CardTitle>
                  </div>
                  <div className="flex items-center gap-2">
                    {featureResult && !featureLoading && (
                      <Button variant="ghost" size="sm" onClick={handleCopy} className="gap-1.5">
                        {copied ? <Check className="h-3.5 w-3.5 text-success" /> : <Copy className="h-3.5 w-3.5" />}
                        <span className="text-xs">{copied ? 'Copied' : 'Copy'}</span>
                      </Button>
                    )}
                    <Button variant="ghost" size="sm" onClick={closeModal}>
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="max-h-[60vh] overflow-y-auto">
                  {renderFeatureContent()}
                </CardContent>
              </Card>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </AnimatedPage>
  )
}
