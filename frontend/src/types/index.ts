export interface CVAnalysisResult {
  filename: string
  ats_score: number | null
  skills_extracted: string[]
  job_matches: number
  report: string | null
}

export interface SSEEvent {
  step: string
  status?: string
  error?: string
  result?: CVAnalysisResult
}

export interface Job {
  id: number
  title: string
  company: string
  location?: string
  published_date?: string
  description?: string
}

export interface AnalysisHistory {
  id: string
  filename: string
  ats_score: number | null
  skills_extracted: string[]
  created_at: string
}
