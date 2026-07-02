const API_BASE_URL = import.meta.env.VITE_API_URL || ''
const API_BASE = `${API_BASE_URL}/api/v1`

let _token: string | null = null

export function setAuthToken(token: string | null) {
  _token = token
}

export function getAuthToken(): string | null {
  return _token
}

function authHeaders(): Record<string, string> {
  return _token ? { Authorization: `Bearer ${_token}` } : {}
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

  analyzeCVStream: (file: File, onEvent: (event: any) => void, onError: (err: Error) => void): AbortController => {
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
    return handleResponse<{ status: string; data: any[] }>(res)
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
}
