import { describe, it, expect, beforeEach, vi } from 'vitest'
import { api, setAuthToken, getAuthToken, ApiError } from '@/api/client'

const mockStorage: Record<string, string> = {}
vi.stubGlobal('sessionStorage', {
  getItem: (key: string) => mockStorage[key] ?? null,
  setItem: (key: string, val: string) => { mockStorage[key] = val },
  removeItem: (key: string) => { delete mockStorage[key] },
  clear: () => { Object.keys(mockStorage).forEach(k => delete mockStorage[k]) },
})

beforeEach(() => {
  Object.keys(mockStorage).forEach(k => delete mockStorage[k])
  vi.restoreAllMocks()
})

describe('ApiError', () => {
  it('stores status and message', () => {
    const err = new ApiError(404, 'Not found')
    expect(err.status).toBe(404)
    expect(err.message).toBe('Not found')
    expect(err.name).toBe('ApiError')
  })
})

describe('setAuthToken / getAuthToken', () => {
  it('stores and retrieves token from sessionStorage', () => {
    setAuthToken('test-token')
    expect(getAuthToken()).toBe('test-token')
  })

  it('removes token when set to null', () => {
    setAuthToken('test-token')
    setAuthToken(null)
    expect(getAuthToken()).toBeNull()
  })
})

function mockFetch(status: number, body: unknown, ok?: boolean) {
  return vi.mocked(fetch).mockResolvedValueOnce({
    ok: ok ?? (status >= 200 && status < 300),
    status,
    json: () => Promise.resolve(body),
    statusText: 'Mocked',
  } as Response)
}

async function expectRejectsAsync(fn: () => Promise<unknown>, expectedStatus: number, expectedMessage: string) {
  try {
    await fn()
    expect.unreachable('Expected error to be thrown')
  } catch (err) {
    expect(err).toBeInstanceOf(ApiError)
    expect((err as ApiError).status).toBe(expectedStatus)
    expect((err as ApiError).message).toContain(expectedMessage)
  }
}

describe('api.health', () => {
  it('returns health status on success', async () => {
    vi.spyOn(globalThis, 'fetch')
    mockFetch(200, { status: 'healthy', database: 'connected' })

    const result = await api.health()
    expect(result.status).toBe('healthy')
    expect(result.database).toBe('connected')
  })

  it('throws ApiError on failure', async () => {
    vi.spyOn(globalThis, 'fetch')
    mockFetch(500, { detail: 'Server error' })

    await expectRejectsAsync(() => api.health(), 500, 'Server error')
  })
})

describe('api.login', () => {
  it('sends form-encoded body and returns token', async () => {
    vi.spyOn(globalThis, 'fetch')
    mockFetch(200, { access_token: 'jwt-token', token_type: 'bearer' })

    const result = await api.login('test@test.com', 'pass123')
    expect(result.access_token).toBe('jwt-token')
    expect(result.token_type).toBe('bearer')
  })
})

describe('api.register', () => {
  it('sends JSON body and returns user', async () => {
    vi.spyOn(globalThis, 'fetch')
    mockFetch(201, { id: 1, email: 'a@b.com', is_active: true, is_superuser: false, is_verified: false })

    const result = await api.register('a@b.com', 'Str0ng!Pass')
    expect(result.id).toBe(1)
    expect(result.email).toBe('a@b.com')
  })
})

describe('api.getLatestJobs', () => {
  it('returns jobs list', async () => {
    vi.spyOn(globalThis, 'fetch')
    const jobs = [{ job_title: 'Python Dev', job_link: 'http://example.com', platform: 'test' }]
    mockFetch(200, { status: 'success', data: jobs })

    const result = await api.getLatestJobs(5)
    expect(result.status).toBe('success')
    expect(result.data).toHaveLength(1)
    expect(result.data[0].job_title).toBe('Python Dev')
  })
})

describe('api.getHistory', () => {
  it('sends auth header and returns history', async () => {
    vi.spyOn(globalThis, 'fetch')
    setAuthToken('my-token')
    const records = [{ id: 1, filename: 'cv.pdf', ats_score: 85, skills_extracted: ['python'], job_matches: 3, created_at: '2025-01-01T00:00:00' }]
    mockFetch(200, { status: 'success', data: records })

    const result = await api.getHistory(10)
    expect(result.data).toHaveLength(1)
    const call = vi.mocked(fetch).mock.calls[0]
    expect(call[1]?.headers).toMatchObject({ Authorization: 'Bearer my-token' })
  })

  it('throws on 401', async () => {
    vi.spyOn(globalThis, 'fetch')
    mockFetch(401, { detail: 'Unauthorized' })

    await expectRejectsAsync(() => api.getHistory(), 401, 'Unauthorized')
  })
})

describe('api.getStats', () => {
  it('returns stats', async () => {
    vi.spyOn(globalThis, 'fetch')
    mockFetch(200, { status: 'success', data: { total_analyses: 5, average_score: 80, total_job_matches: 10, last_analysis: '2d ago' } })

    const result = await api.getStats()
    expect(result.data.total_analyses).toBe(5)
    expect(result.data.last_analysis).toBe('2d ago')
  })
})

describe('api.matchJob', () => {
  it('sends JSON body', async () => {
    vi.spyOn(globalThis, 'fetch')
    setAuthToken('tkn')
    const response = { match_score: 90, matched_skills: ['python'], missing_skills: [], improvement_tips: ['add more'], keyword_coverage: 0.8, cv_text: '' }
    mockFetch(200, response)

    const result = await api.matchJob('desc', 'cv text')
    expect(result.match_score).toBe(90)
    const call = vi.mocked(fetch).mock.calls[0]
    const body = JSON.parse(call[1]?.body as string)
    expect(body.job_description).toBe('desc')
    expect(body.cv_text).toBe('cv text')
  })
})

describe('api.matchJobFile', () => {
  it('sends multipart form', async () => {
    vi.spyOn(globalThis, 'fetch')
    setAuthToken('tkn')
    mockFetch(200, { match_score: 80, matched_skills: [], missing_skills: [], improvement_tips: [], keyword_coverage: 0.5, cv_text: '' })

    const file = new File(['content'], 'cv.pdf', { type: 'application/pdf' })
    await api.matchJobFile(file, 'job desc')
    const call = vi.mocked(fetch).mock.calls[0]
    expect(call[1]?.body).toBeInstanceOf(FormData)
  })
})

describe('api.analyzeCVStream', () => {
  it('parses SSE events and calls onEvent', async () => {
    vi.spyOn(globalThis, 'fetch')
    const onEvent = vi.fn()
    const onError = vi.fn()

    const encoder = new TextEncoder()
    const stream = new ReadableStream({
      start(controller) {
        controller.enqueue(encoder.encode('data: {"step":"parse","status":"complete"}\n\n'))
        controller.enqueue(encoder.encode('data: {"step":"analyze","status":"complete"}\n\n'))
        controller.enqueue(encoder.encode('data: {"step":"complete","result":{"ats_score":85}}\n\n'))
        controller.close()
      },
    })

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      body: stream,
      json: () => Promise.resolve({}),
    } as Response)

    const controller = api.analyzeCVStream(new File(['x'], 'test.pdf'), onEvent, onError)
    await new Promise((r) => setTimeout(r, 50))
    controller.abort()

    expect(onEvent).toHaveBeenCalledTimes(3)
    expect(onEvent).toHaveBeenCalledWith({ step: 'parse', status: 'complete' })
    expect(onEvent).toHaveBeenCalledWith({ step: 'complete', result: { ats_score: 85 } })
    expect(onError).not.toHaveBeenCalled()
  })

  it('calls onError on non-ok response', async () => {
    vi.spyOn(globalThis, 'fetch')
    const onEvent = vi.fn()
    const onError = vi.fn()

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: false,
      status: 400,
      json: () => Promise.resolve({ detail: 'Bad file' }),
    } as Response)

    api.analyzeCVStream(new File(['x'], 'test.pdf'), onEvent, onError)
    await new Promise((r) => setTimeout(r, 50))

    expect(onError).toHaveBeenCalledWith(expect.objectContaining({ status: 400, message: 'Bad file' }))
    expect(onEvent).not.toHaveBeenCalled()
  })
})

describe('api.analyzeCV', () => {
  it('returns analysis result', async () => {
    vi.spyOn(globalThis, 'fetch')
    setAuthToken('tkn')
    mockFetch(200, { status: 'success', filename: 'cv.pdf', ats_score: 85, skills_extracted: ['python'], job_matches: 3, report: 'Good CV' })

    const result = await api.analyzeCV(new File(['x'], 'cv.pdf'))
    expect(result.ats_score).toBe(85)
    expect(result.report).toBe('Good CV')
  })
})

describe('api.tailorResume', () => {
  it('returns tailored resume', async () => {
    vi.spyOn(globalThis, 'fetch')
    setAuthToken('tkn')
    mockFetch(200, { tailored_resume: 'New resume text' })

    const result = await api.tailorResume('desc', 'cv')
    expect(result.tailored_resume).toBe('New resume text')
  })
})

describe('api.standOut', () => {
  it('returns suggestions', async () => {
    vi.spyOn(globalThis, 'fetch')
    setAuthToken('tkn')
    mockFetch(200, { unique_selling_points: ['point1'], suggested_certifications: [], project_ideas: [], skill_enhancements: [], overall_strategy: 'strategy' })

    const result = await api.standOut('desc', 'cv')
    expect(result.unique_selling_points).toEqual(['point1'])
  })
})

describe('api.coverLetter', () => {
  it('returns cover letter', async () => {
    vi.spyOn(globalThis, 'fetch')
    setAuthToken('tkn')
    mockFetch(200, { cover_letter: 'Dear Hiring Manager...' })

    const result = await api.coverLetter('desc', 'cv')
    expect(result.cover_letter).toContain('Dear')
  })
})

describe('api.getRewriteSuggestions', () => {
  it('uploads file and returns rewrites', async () => {
    vi.spyOn(globalThis, 'fetch')
    setAuthToken('tkn')
    mockFetch(200, { overall_assessment: 'Good', rewrites: [{ original: 'old', issue: 'weak', improved: 'new' }], quick_wins: ['fix'] })

    const result = await api.getRewriteSuggestions(new File(['x'], 'cv.pdf'))
    expect(result.overall_assessment).toBe('Good')
    expect(result.rewrites).toHaveLength(1)
  })
})

describe('api.getMarketDemand', () => {
  it('returns market data', async () => {
    vi.spyOn(globalThis, 'fetch')
    setAuthToken('tkn')
    mockFetch(200, { status: 'success', data: [{ skill: 'Python', job_count: 100, demand_level: 'high' }] })

    const result = await api.getMarketDemand()
    expect(result.data).toHaveLength(1)
    expect(result.data[0].skill).toBe('Python')
  })
})
