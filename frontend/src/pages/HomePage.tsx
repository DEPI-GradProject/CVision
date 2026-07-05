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
import { AnimatedPage } from '@/components/AnimatedPage'
import { cn } from '@/lib/utils'

const features = [
  {
    icon: FileSearch,
    title: 'Smart Parsing',
    description: 'AI extracts skills, experience, and education from any CV format with precision.',
    color: 'from-[#007aff] to-[#5856d6]',
  },
  {
    icon: BarChart3,
    title: 'ATS Scoring',
    description: 'Get a detailed compatibility score and know exactly where you stand.',
    color: 'from-[#34c759] to-[#30d158]',
  },
  {
    icon: Brain,
    title: 'Job Matching',
    description: 'Find the best-fitting roles from thousands of live listings.',
    color: 'from-[#ff9500] to-[#ff9f0a]',
  },
  {
    icon: Users,
    title: 'Market Insights',
    description: 'Understand demand for your skills and identify growth opportunities.',
    color: 'from-[#007aff] to-[#0a84ff]',
  },
]

const steps = [
  { icon: Upload, title: 'Upload CV', description: 'Drop your PDF or DOCX file, or paste your text.' },
  { icon: Brain, title: 'AI Analysis', description: 'Our agents parse, score, and match in real-time.' },
  { icon: FileText, title: 'Get Results', description: 'View ATS score, matched jobs, and full report.' },
]

function SpringDiv({
  children,
  className,
  delay = 0,
}: {
  children: React.ReactNode
  className?: string
  delay?: number
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.7, delay, ease: [0.16, 1, 0.3, 1] }}
      className={className}
    >
      {children}
    </motion.div>
  )
}

export function HomePage() {
  return (
    <AnimatedPage>
      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <section className="flex min-h-[calc(100vh-5rem)] flex-col items-center justify-center pb-16 pt-20">
          <SpringDiv delay={0}>
            <Badge
              variant="default"
              className="mb-6 rounded-full px-5 py-2 text-xs font-medium tracking-wide uppercase"
            >
              <Sparkles className="mr-1.5 h-3.5 w-3.5" />
              AI-Powered CV Analysis
            </Badge>
          </SpringDiv>

          <SpringDiv delay={0.1} className="max-w-3xl text-center">
            <h1 className="text-5xl font-bold tracking-tight sm:text-6xl lg:text-7xl/none leading-[1.05]">
              Transform Your CV
              <br />
              <span className="bg-gradient-to-r from-[#007aff] via-[#0a84ff] to-[#5856d6] bg-clip-text text-transparent">
                Career Opportunities
              </span>
            </h1>
          </SpringDiv>

          <SpringDiv delay={0.2} className="mt-5 max-w-xl text-center">
            <p className="text-lg leading-relaxed text-text-secondary sm:text-xl">
              Upload your CV and let AI analyze, score, and match it against thousands of jobs.
              Get actionable insights to land your dream role.
            </p>
          </SpringDiv>

          <SpringDiv delay={0.3} className="mt-8 flex flex-col items-center gap-4 sm:flex-row">
            <Link to="/upload">
              <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}>
                <Button variant="gradient" size="xl" className="text-base">
                  <Upload className="h-5 w-5" />
                  Analyze Your CV
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </motion.div>
            </Link>
            <Link to="/dashboard">
              <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}>
                <Button variant="outline" size="xl" className="text-base">
                  View Dashboard
                </Button>
              </motion.div>
            </Link>
          </SpringDiv>

          <SpringDiv delay={0.4} className="mt-8">
            <div className="flex items-center gap-5 text-sm text-text-muted">
              <span className="flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5" /> PDF & DOCX
              </span>
              <span className="h-1 w-1 rounded-full bg-border" />
              <span>Free to use</span>
              <span className="h-1 w-1 rounded-full bg-border" />
              <span>10MB max</span>
            </div>
          </SpringDiv>
        </section>

        <section className="pb-28">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature, i) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-40px' }}
                transition={{ duration: 0.5, delay: i * 0.08, ease: [0.16, 1, 0.3, 1] }}
              >
                <motion.div
                  whileHover={{ y: -4, scale: 1.01 }}
                  className="group h-full rounded-3xl border border-border/50 bg-white/60 dark:bg-white/[0.03] backdrop-blur-xl p-7 transition-all duration-300 hover:border-border/80 hover:bg-white/80 dark:hover:bg-white/[0.06] hover:shadow-glass-lg dark:hover:shadow-glass-dark"
                >
                  <div
                    className={cn(
                      'mb-5 flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br shadow-lg',
                      feature.color,
                    )}
                  >
                    <feature.icon className="h-5 w-5 text-white" />
                  </div>
                  <h3 className="mb-1.5 text-base font-semibold">{feature.title}</h3>
                  <p className="text-sm leading-relaxed text-text-secondary">
                    {feature.description}
                  </p>
                </motion.div>
              </motion.div>
            ))}
          </div>
        </section>

        <section className="section-separator pb-28 pt-20">
          <div className="mx-auto mb-16 max-w-xl text-center">
            <SpringDiv>
              <h2 className="text-4xl font-bold tracking-tight sm:text-5xl">How It Works</h2>
              <p className="mt-4 text-lg text-text-secondary">
                Three simple steps to transform your job search
              </p>
            </SpringDiv>
          </div>

          <div className="grid gap-6 md:grid-cols-3">
            {steps.map((step, i) => (
              <motion.div
                key={step.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: '-40px' }}
                transition={{ duration: 0.5, delay: i * 0.12, ease: [0.16, 1, 0.3, 1] }}
                className="relative"
              >
                {i < steps.length - 1 && (
                  <div className="absolute left-[60%] top-10 hidden h-px w-[80%] md:block">
                    <svg className="w-full" height="1" viewBox="0 0 100 1" preserveAspectRatio="none">
                      <line x1="0" y1="0" x2="100" y2="0" stroke="currentColor" strokeDasharray="4 4" className="text-border" strokeWidth="0.5" />
                    </svg>
                  </div>
                )}
                <div className="flex flex-col items-center text-center">
                  <div className="relative mb-5 flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-[#007aff] to-[#005bbf] shadow-xl shadow-[#007aff]/20">
                    <motion.div
                      whileHover={{ scale: 1.08, rotate: -5 }}
                      transition={{ type: 'spring', stiffness: 300 }}
                    >
                      <step.icon className="h-8 w-8 text-white" />
                    </motion.div>
                  </div>
                  <div className="mb-2 text-xs font-semibold tracking-widest text-text-muted uppercase">
                    Step {i + 1}
                  </div>
                  <h3 className="mb-1.5 text-xl font-semibold">{step.title}</h3>
                  <p className="text-sm text-text-secondary">{step.description}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </section>

        <section className="section-separator pb-28 pt-20 text-center">
          <SpringDiv>
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Ready to elevate your career?
            </h2>
            <p className="mt-3 text-lg text-text-secondary">
              Join thousands of job seekers who landed their dream roles with CVision.
            </p>
            <div className="mt-8">
              <Link to="/upload">
                <motion.div whileHover={{ scale: 1.02 }} whileTap={{ scale: 0.97 }}>
                  <Button variant="gradient" size="xl" className="text-base">
                    Get Started Free
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                </motion.div>
              </Link>
            </div>
          </SpringDiv>
        </section>
      </div>
    </AnimatedPage>
  )
}
