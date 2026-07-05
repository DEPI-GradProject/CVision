import type { RawJob, SSEEvent } from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_URL || ''
const API_BASE = `${API_BASE_URL}/api/v1`

const TOKEN_KEY = 'access_token'

export function setAuthToken(token: string | null) {
  if (token) {
    sessionStorage.setItem(TOKEN_KEY, token)
  } else {
    sessionStorage.removeItem(TOKEN_KEY)
  }
}

export function getAuthToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY)
}

function authHeaders(): Record<string, string> {
  const token = sessionStorage.getItem(TOKEN_KEY)
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
    this.name = 'ApiError'
  }
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }))
    throw new ApiError(res.status, body.detail || 'An error occurred')
  }
  return res.json()
}

export const api = {
  health: async () => {
    const res = await fetch(`${API_BASE}/health`)
    return handleResponse<{ status: string; database: string }>(res)
  },

  login: async (email: string, password: string) => {
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)
    const res = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: form,
    })
    const data = await handleResponse<{ access_token: string; token_type: string }>(res)
    return data
  },

  register: async (email: string, password: string) => {
    const res = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    })
    return handleResponse<{ id: number; email: string; is_active: boolean; is_superuser: boolean; is_verified: boolean }>(res)
  },

  logout: async () => {
    const res = await fetch(`${API_BASE_URL}/auth/logout`, {
      method: 'POST',
      headers: { ...authHeaders() },
    })
    if (!res.ok && res.status !== 401) {
      throw new ApiError(res.status, 'Logout failed')
    }
  },

  me: async () => {
    const res = await fetch(`${API_BASE_URL}/auth/me`, {
      headers: { ...authHeaders() },
    })
    return handleResponse<{ id: number; email: string; is_active: boolean; is_superuser: boolean; is_verified: boolean }>(res)
  },

  analyzeCV: async (file: File) => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${API_BASE}/analyze-cv`, {
      method: 'POST',
      headers: { ...authHeaders() },
      body: form,
    })
    return handleResponse<{
      status: string
      filename: string
      ats_score: number | null
      skills_extracted: string[]
      job_matches: number
      report: string | null
    }>(res)
  },

  analyzeCVStream: (file: File, onEvent: (event: SSEEvent) => void, onError: (err: Error) => void): AbortController => {
    const controller = new AbortController()
    const form = new FormData()
    form.append('file', file)

    fetch(`${API_BASE}/analyze-cv/stream`, {
      method: 'POST',
      headers: { ...authHeaders() },
      body: form,
      signal: controller.signal,
    }).then(async (res) => {
      if (!res.ok) {
        const body = await res.json().catch(() => ({ detail: res.statusText }))
        onError(new ApiError(res.status, body.detail || 'Stream failed'))
        return
      }

      const reader = res.body?.getReader()
      if (!reader) {
        onError(new Error('No response body'))
        return
      }

      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              onEvent(data)
            } catch {
              // skip malformed events
            }
          }
        }
      }
    }).catch((err) => {
      if (err.name !== 'AbortError') onError(err)
    })

    return controller
  },

  getLatestJobs: async (limit = 20) => {
    const res = await fetch(`${API_BASE}/jobs/latest?limit=${limit}`)
    return handleResponse<{ status: string; data: RawJob[] }>(res)
  },

  getHistory: async (limit = 50) => {
    const res = await fetch(`${API_BASE}/history?limit=${limit}`, {
      headers: { ...authHeaders() },
    })
    return handleResponse<{
      status: string
      data: Array<{
        id: number
        filename: string
        ats_score: number | null
        skills_extracted: string[]
        job_matches: number | null
        created_at: string
      }>
    }>(res)
  },

  getStats: async () => {
    const res = await fetch(`${API_BASE}/stats`, {
      headers: { ...authHeaders() },
    })
    return handleResponse<{
      status: string
      data: {
        total_analyses: number
        average_score: number
        total_job_matches: number
        last_analysis: string
      }
    }>(res)
  },

  matchJob: async (jobDescription: string, cvText: string) => {
    const res = await fetch(`${API_BASE}/match-job`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ job_description: jobDescription, cv_text: cvText }),
    })
    return handleResponse<{
      match_score: number
      matched_skills: string[]
      missing_skills: string[]
      improvement_tips: string[]
      keyword_coverage: number
      cv_text: string
    }>(res)
  },

  matchJobFile: async (file: File, jobDescription: string) => {
    const form = new FormData()
    form.append('file', file)
    form.append('job_description', jobDescription)
    const res = await fetch(`${API_BASE}/match-job/file`, {
      method: 'POST',
      headers: { ...authHeaders() },
      body: form,
    })
    return handleResponse<{
      match_score: number
      matched_skills: string[]
      missing_skills: string[]
      improvement_tips: string[]
      keyword_coverage: number
      cv_text: string
    }>(res)
  },

  tailorResume: async (jobDescription: string, cvText: string) => {
    const res = await fetch(`${API_BASE}/tailor-resume`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ job_description: jobDescription, cv_text: cvText }),
    })
    return handleResponse<{ tailored_resume: string }>(res)
  },

  standOut: async (jobDescription: string, cvText: string) => {
    const res = await fetch(`${API_BASE}/stand-out`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ job_description: jobDescription, cv_text: cvText }),
    })
    return handleResponse<{
      unique_selling_points: string[]
      suggested_certifications: string[]
      project_ideas: string[]
      skill_enhancements: string[]
      overall_strategy: string
    }>(res)
  },

  coverLetter: async (jobDescription: string, cvText: string) => {
    const res = await fetch(`${API_BASE}/cover-letter`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ job_description: jobDescription, cv_text: cvText }),
    })
    return handleResponse<{ cover_letter: string }>(res)
  },

  getRewriteSuggestions: async (file: File) => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${API_BASE}/rewrite-suggestions`, {
      method: 'POST',
      headers: { ...authHeaders() },
      body: form,
    })
    return handleResponse<{
      overall_assessment: string
      rewrites: Array<{ original: string; issue: string; improved: string }>
      quick_wins: string[]
    }>(res)
  },

  getMarketDemand: async () => {
    const res = await fetch(`${API_BASE}/skills/market-demand`, {
      headers: { ...authHeaders() },
    })
    return handleResponse<{
      status: string
      data: Array<{
        skill: string
        job_count: number
        demand_level: string
      }>
    }>(res)
  },
}
