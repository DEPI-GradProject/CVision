import { motion } from 'framer-motion'
import { Sparkles } from 'lucide-react'

export function Footer() {
  return (
    <motion.footer
      initial={{ opacity: 0 }}
      whileInView={{ opacity: 1 }}
      viewport={{ once: true }}
      className="relative z-10 border-t border-border/50 bg-background"
    >
      <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-4 px-4 py-8 sm:flex-row sm:px-6 lg:px-8">
        <motion.div
          className="flex items-center gap-2 text-sm text-text-muted"
          whileHover={{ color: 'var(--color-text-primary)' }}
        >
          <Sparkles className="h-3.5 w-3.5" />
          <span>CVision — AI-Powered CV Analysis</span>
        </motion.div>
        <p className="text-sm text-text-muted">
          &copy; {new Date().getFullYear()} CVision. All rights reserved.
        </p>
      </div>
    </motion.footer>
  )
}
