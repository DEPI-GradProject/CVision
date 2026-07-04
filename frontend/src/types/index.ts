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
  id: number
  filename: string
  ats_score: number | null
  skills_extracted: string[]
  job_matches: number | null
  created_at: string
}

export interface DashboardStats {
  total_analyses: number
  average_score: number
  total_job_matches: number
  last_analysis: string
}

export interface User {
  id: number
  email: string
  is_active: boolean
  is_superuser: boolean
  is_verified: boolean
}

export interface JobMatchResult {
  match_score: number
  matched_skills: string[]
  missing_skills: string[]
  improvement_tips: string[]
}

export interface MarketSkill {
  skill: string
  job_count: number
  demand_level: "high" | "medium" | "low"
}
