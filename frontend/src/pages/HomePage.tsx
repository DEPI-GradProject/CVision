import {
  ArrowRight,
  BarChart3,
  Brain,
  FileSearch,
  FileText,
  Sparkles,
  Upload,
  Users,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { ScrollReveal } from '@/components/ScrollReveal'
import { AnimatedPage } from '@/components/AnimatedPage'
import {
  fadeInUp,
  staggerContainer,
  staggerItem,
  scaleIn,
  cardHover,
} from '@/lib/animations'

const features = [
  {
    icon: FileSearch,
    title: 'Smart Parsing',
    description: 'Extract skills, experience, and education from any CV format with AI-powered precision.',
    gradient: 'from-violet-500/20 to-purple-500/20',
    iconColor: 'text-violet-400',
  },
  {
    icon: BarChart3,
    title: 'ATS Scoring',
    description: 'Get a detailed compatibility score against top job descriptions in your field.',
    gradient: 'from-emerald-500/20 to-teal-500/20',
    iconColor: 'text-emerald-400',
  },
  {
    icon: Brain,
    title: 'Job Matching',
    description: 'Find the best-fitting roles from our curated database of live job listings.',
    gradient: 'from-amber-500/20 to-orange-500/20',
    iconColor: 'text-amber-400',
  },
  {
    icon: Users,
    title: 'Insights',
    description: 'Understand market demand for your skills and identify growth opportunities.',
    gradient: 'from-sky-500/20 to-blue-500/20',
    iconColor: 'text-sky-400',
  },
]

const steps = [
  { number: '01', title: 'Upload CV', description: 'Drag & drop your PDF or DOCX file.' },
  { number: '02', title: 'AI Analysis', description: 'Our agents parse, score, and match in real-time.' },
  { number: '03', title: 'Get Results', description: 'View your ATS score, matched jobs, and full report.' },
]

function FloatingOrb({ className, delay = 0 }: { className: string; delay?: number }) {
  return (
    <motion.div
      className={cn('pointer-events-none absolute rounded-full blur-[120px]', className)}
      animate={{
        y: [0, -30, 0, 20, 0],
        x: [0, 20, -10, 10, 0],
        scale: [1, 1.05, 0.95, 1.02, 1],
      }}
      transition={{ duration: 10 + delay, repeat: Infinity, ease: 'easeInOut' }}
    />
  )
}

import { cn } from '@/lib/utils'

export function HomePage() {
  return (
    <AnimatedPage>
      <div className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <FloatingOrb className="-top-40 right-0 h-[500px] w-[500px] bg-violet-600/10 dark:bg-violet-600/10" delay={0} />
          <FloatingOrb className="-bottom-40 left-0 h-[400px] w-[400px] bg-indigo-500/10 dark:bg-indigo-500/10" delay={3} />
          <FloatingOrb className="top-1/3 left-1/4 h-[300px] w-[300px] bg-purple-500/10 dark:bg-purple-500/10" delay={6} />
        </div>

        <section className="relative mx-auto max-w-7xl px-4 pb-20 pt-16 sm:px-6 lg:px-8">
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="mx-auto max-w-3xl text-center"
          >
            <motion.div variants={staggerItem}>
              <Badge variant="default" className="mb-6 px-4 py-1.5 text-sm">
                <Sparkles className="mr-1.5 h-3.5 w-3.5" />
                AI-Powered CV Analysis
              </Badge>
            </motion.div>

            <motion.h1
              variants={staggerItem}
              className="text-4xl font-bold tracking-tight sm:text-6xl lg:text-7xl"
            >
              Transform Your CV Into{' '}
              <span className="bg-gradient-to-r from-violet-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent animate-gradient">
                Career Opportunities
              </span>
            </motion.h1>

            <motion.p
              variants={staggerItem}
              className="mt-6 text-lg leading-relaxed text-text-secondary sm:text-xl"
            >
              Upload your CV and let AI analyze, score, and match it against thousands of jobs.
              Get actionable insights to land your dream role.
            </motion.p>

            <motion.div
              variants={staggerItem}
              className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row"
            >
              <Link to="/upload">
                <motion.div
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.97 }}
                >
                  <Button variant="gradient" size="xl" className="animate-pulse-glow group">
                    <Upload className="h-5 w-5 transition-transform group-hover:-translate-y-0.5" />
                    Analyze Your CV
                    <ArrowRight className="h-4 w-4 opacity-0 -translate-x-2 transition-all group-hover:opacity-100 group-hover:translate-x-0" />
                  </Button>
                </motion.div>
              </Link>
              <Link to="/dashboard">
                <motion.div whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}>
                  <Button variant="outline" size="xl">
                    View Dashboard
                  </Button>
                </motion.div>
              </Link>
            </motion.div>

            <motion.div
              variants={staggerItem}
              className="mt-8 flex items-center justify-center gap-6 text-sm text-text-muted"
            >
              <span className="flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5" /> PDF & DOCX
              </span>
              <span className="h-1 w-1 rounded-full bg-border" />
              <span>Free to use</span>
              <span className="h-1 w-1 rounded-full bg-border" />
              <span>10MB max</span>
            </motion.div>
          </motion.div>
        </section>

        <section className="relative mx-auto max-w-7xl px-4 pb-24 sm:px-6 lg:px-8">
          <motion.div
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-60px' }}
            className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4"
          >
            {features.map((feature) => (
              <motion.div key={feature.title} variants={staggerItem}>
                <motion.div
                  whileHover="hover"
                  initial="rest"
                  variants={cardHover}
                  className="group h-full rounded-2xl border border-border bg-surface/80 backdrop-blur-xl shadow-xl transition-colors hover:bg-surface"
                >
                  <CardContent className="p-6">
                    <motion.div
                      className={cn(
                        'mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-primary-muted transition-all',
                        feature.iconColor,
                      )}
                      whileHover={{ rotate: [0, -10, 10, -5, 0], transition: { duration: 0.5 } }}
                    >
                      <feature.icon className="h-6 w-6" />
                    </motion.div>
                    <h3 className="mb-2 font-semibold">{feature.title}</h3>
                    <p className="text-sm leading-relaxed text-text-secondary">
                      {feature.description}
                    </p>
                  </CardContent>
                </motion.div>
              </motion.div>
            ))}
          </motion.div>
        </section>

        <section className="relative border-t border-border/50 bg-surface/50 pb-24 pt-20">
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <ScrollReveal>
              <div className="mx-auto mb-16 max-w-2xl text-center">
                <h2 className="text-3xl font-bold sm:text-4xl">How It Works</h2>
                <p className="mt-4 text-text-secondary">
                  Three simple steps to transform your job search
                </p>
              </div>
            </ScrollReveal>

            <div className="grid gap-8 md:grid-cols-3">
              {steps.map((step, i) => (
                <ScrollReveal key={step.number} delay={i * 100}>
                  <motion.div
                    className="relative text-center"
                    whileHover={{ y: -5 }}
                    transition={{ type: 'spring', stiffness: 300 }}
                  >
                    {i < steps.length - 1 && (
                      <motion.div
                        initial={{ scaleX: 0 }}
                        whileInView={{ scaleX: 1 }}
                        viewport={{ once: true }}
                        className="absolute left-[60%] top-8 hidden h-px w-[80%] origin-left border-t border-dashed border-border md:block"
                      />
                    )}
                    <motion.div
                      className="relative mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-violet-600 to-indigo-500 text-lg font-bold text-white shadow-lg shadow-violet-500/25"
                      whileHover={{ scale: 1.1, rotate: [0, -5, 5, 0] }}
                      transition={{ type: 'spring', stiffness: 400 }}
                    >
                      {step.number}
                    </motion.div>
                    <h3 className="mb-2 text-xl font-semibold">{step.title}</h3>
                    <p className="text-text-secondary">{step.description}</p>
                  </motion.div>
                </ScrollReveal>
              ))}
            </div>
          </div>
        </section>
      </div>
    </AnimatedPage>
  )
}
