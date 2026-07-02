import { useState, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { FileText, Upload, X, AlertCircle, CheckCircle2, File, FileWarning } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { AnimatedPage } from '@/components/AnimatedPage'
import { ScrollReveal } from '@/components/ScrollReveal'
import { useToast } from '@/components/Toast'
import { cn } from '@/lib/utils'
import { fadeInUp, staggerContainer, staggerItem } from '@/lib/animations'

const ALLOWED_EXTENSIONS = ['.pdf', '.docx']
const MAX_SIZE = 10 * 1024 * 1024

export function UploadPage() {
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [dragActive, setDragActive] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const { toast } = useToast()

  const validateFile = useCallback((f: File): string | null => {
    const ext = '.' + f.name.split('.').pop()?.toLowerCase()
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return 'Unsupported file type. Please use PDF or DOCX.'
    }
    if (f.size > MAX_SIZE) {
      return 'File too large. Maximum size is 10MB.'
    }
    return null
  }, [])

  const handleFile = useCallback((f: File) => {
    setError(null)
    const err = validateFile(f)
    if (err) {
      setError(err)
      setFile(null)
      toast(err, 'error')
    } else {
      setFile(f)
      toast(`"${f.name}" selected`, 'success')
    }
  }, [validateFile, toast])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }, [handleFile])

  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f) handleFile(f)
  }, [handleFile])

  const handleSubmit = () => {
    if (!file) return
    setUploading(true)
    toast('Starting CV analysis...', 'info')
    setTimeout(() => {
      navigate('/analysis', { state: { file } })
    }, 400)
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <AnimatedPage>
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <motion.div
          variants={staggerContainer}
          initial="hidden"
          animate="visible"
          className="mx-auto max-w-2xl text-center"
        >
          <motion.div variants={staggerItem}>
            <h1 className="text-3xl font-bold sm:text-4xl">Upload Your CV</h1>
          </motion.div>
          <motion.div variants={staggerItem}>
            <p className="mt-3 text-text-secondary">
              Drop your file below and let AI analyze your resume against thousands of jobs
            </p>
          </motion.div>
        </motion.div>

        <div className="mx-auto mt-12 max-w-xl">
          <motion.div
            variants={fadeInUp}
            initial="hidden"
            animate="visible"
          >
            <Card>
              <CardHeader>
                <CardTitle>Choose File</CardTitle>
                <CardDescription>PDF or DOCX up to 10MB</CardDescription>
              </CardHeader>
              <CardContent>
                <motion.div
                  onDragOver={(e) => { e.preventDefault(); setDragActive(true) }}
                  onDragLeave={() => setDragActive(false)}
                  onDrop={handleDrop}
                  onClick={() => inputRef.current?.click()}
                  whileHover={!file ? { scale: 1.01 } : {}}
                  className={cn(
                    'relative flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-12 transition-all',
                    dragActive
                      ? 'border-primary bg-primary-muted'
                      : file
                        ? 'border-success bg-emerald-500/5'
                        : 'border-border hover:border-primary/50 hover:bg-surface-light',
                  )}
                >
                  <input
                    ref={inputRef}
                    type="file"
                    accept=".pdf,.docx"
                    onChange={handleChange}
                    className="hidden"
                  />

                  <AnimatePresence mode="wait">
                    {file ? (
                      <motion.div
                        key="file-selected"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        className="text-center"
                      >
                        <motion.div
                          className="mb-4 mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-500/10"
                          animate={{ rotate: [0, 0, 0, 0, 0] }}
                        >
                          <CheckCircle2 className="h-8 w-8 text-success" />
                        </motion.div>
                        <p className="font-medium">{file.name}</p>
                        <p className="mt-1 text-sm text-text-muted">{formatSize(file.size)}</p>
                        <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                          <Button
                            variant="ghost"
                            size="sm"
                            className="mt-4"
                            onClick={(e) => { e.stopPropagation(); setFile(null); setError(null) }}
                          >
                            <X className="mr-1 h-4 w-4" /> Remove
                          </Button>
                        </motion.div>
                      </motion.div>
                    ) : (
                      <motion.div
                        key="empty"
                        initial={{ opacity: 0, scale: 0.8 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.8 }}
                        className="text-center"
                      >
                        <motion.div
                          className="mb-4 mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-primary-muted"
                          animate={dragActive ? { scale: [1, 1.1, 1], transition: { repeat: Infinity, duration: 1 } } : {}}
                        >
                          <Upload className="h-8 w-8 text-primary" />
                        </motion.div>
                        <p className="font-medium">
                          <span className="text-primary">Click to upload</span> or drag and drop
                        </p>
                        <p className="mt-1 text-sm text-text-muted">PDF or DOCX (max 10MB)</p>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>

                <AnimatePresence>
                  {error && (
                    <motion.div
                      initial={{ opacity: 0, y: -10, height: 0 }}
                      animate={{ opacity: 1, y: 0, height: 'auto' }}
                      exit={{ opacity: 0, y: -10, height: 0 }}
                      className="mt-4 flex items-center gap-2 rounded-lg bg-red-500/10 px-4 py-3 text-sm text-error"
                    >
                      <AlertCircle className="h-4 w-4 flex-shrink-0" />
                      {error}
                    </motion.div>
                  )}
                </AnimatePresence>

                <AnimatePresence>
                  {file && !error && (
                    <motion.div
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className="mt-6 flex items-center gap-3 rounded-lg bg-surface-light px-4 py-3 text-sm"
                    >
                      <File className="h-4 w-4 text-primary" />
                      <span className="flex-1 text-text-secondary truncate">{file.name}</span>
                      <span className="text-text-muted">{formatSize(file.size)}</span>
                    </motion.div>
                  )}
                </AnimatePresence>

                <motion.div
                  whileHover={file && !error ? { scale: 1.02 } : {}}
                  whileTap={file && !error ? { scale: 0.98 } : {}}
                >
                  <Button
                    variant="gradient"
                    size="lg"
                    className="mt-6 w-full group"
                    disabled={!file || !!error || uploading}
                    onClick={handleSubmit}
                  >
                    {uploading ? (
                      <>
                        <motion.div
                          animate={{ rotate: 360 }}
                          transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                          className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white"
                        />
                        Starting...
                      </>
                    ) : (
                      <>
                        <Upload className="h-4 w-4 transition-transform group-hover:-translate-y-0.5" />
                        Analyze My CV
                      </>
                    )}
                  </Button>
                </motion.div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </AnimatedPage>
  )
}
