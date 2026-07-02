const API_BASE = '/api/v1'

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

  analyzeCV: async (file: File) => {
    const form = new FormData()
    form.append('file', file)
    const res = await fetch(`${API_BASE}/analyze-cv`, {
      method: 'POST',
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
}
