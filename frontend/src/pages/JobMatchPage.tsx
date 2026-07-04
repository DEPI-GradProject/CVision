import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Briefcase, Upload, AlertCircle, CheckCircle2, XCircle, Lightbulb, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { AnimatedPage } from '@/components/AnimatedPage'
import { cn } from '@/lib/utils'
import { staggerContainer, staggerItem } from '@/lib/animations'
import { api } from '@/api/client'
import type { JobMatchResult } from '@/types'

export function JobMatchPage() {
  const [cvFile, setCvFile] = useState<File | null>(null)
  const [cvText, setCvText] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [result, setResult] = useState<JobMatchResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (!f) return
    setCvFile(f)
    const text = await f.text()
    setCvText(text)
  }

  const handleMatch = async () => {
    if (!cvText.trim() || !jobDescription.trim()) return
    setLoading(true)
    setError(null)
    try {
      const res = await api.matchJob(jobDescription, cvText)
      setResult(res)
    } catch (err: any) {
      setError(err.message || 'Failed to match job')
    } finally {
      setLoading(false)
    }
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

        <div className="mx-auto mt-12 grid max-w-5xl gap-8 lg:grid-cols-2">
          <Card>
            <CardHeader>
              <CardTitle>Your CV</CardTitle>
              <CardDescription>Upload or paste your CV text</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Upload CV file</label>
                <input
                  type="file"
                  accept=".txt,.pdf,.docx"
                  onChange={handleFileChange}
                  className="w-full rounded-lg border border-border bg-surface-light px-3 py-2 text-sm file:mr-3 file:rounded file:border-0 file:bg-primary file:px-3 file:py-1 file:text-sm file:text-white"
                />
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
                disabled={!cvText.trim() || !jobDescription.trim() || loading}
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
              <Card>
                <CardContent className="p-8">
                  <div className="flex flex-col items-center gap-4">
                    <div className="relative flex h-28 w-28 items-center justify-center">
                      <svg className="h-28 w-28 -rotate-90" viewBox="0 0 100 100">
                        <circle cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="8" className="text-border" />
                        <circle
                          cx="50" cy="50" r="45" fill="none" stroke="currentColor" strokeWidth="8"
                          strokeDasharray={`${result.match_score * 2.827} 282.7`}
                          className={cn(
                            'transition-all duration-1000',
                            result.match_score >= 80 ? 'text-success' : result.match_score >= 50 ? 'text-amber-400' : 'text-error',
                          )}
                          strokeLinecap="round"
                        />
                      </svg>
                      <span className={cn(
                        'absolute text-3xl font-bold',
                        result.match_score >= 80 ? 'text-success' : result.match_score >= 50 ? 'text-amber-400' : 'text-error',
                      )}>
                        {result.match_score}%
                      </span>
                    </div>
                    <p className="text-lg font-medium">Match Score</p>
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
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </AnimatedPage>
  )
}
