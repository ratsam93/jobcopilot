export type CareerVaultUpload = {
  parse_status: string
  source_filename: string
  candidate_profile_id: string
  created_profile: {
    full_name?: string | null
    primary_email?: string | null
    target_roles: string[]
    skills: Array<{ skill_name: string }>
    approved_claims: Array<{ claim_text: string }>
  }
}

export type ResumeUploadResult = {
  status: string
  upload_status: string
  profile_id: string
  filename: string
  content_type: string | null
  file_size: number
  text_length: number
  created_at: string
  server_saved: boolean
  parsed_resume: Record<string, unknown>
  warnings: string[]
  raw_response: Record<string, unknown>
}

export type CampaignCreate = {
  campaign_id: string
  campaign_name: string
  status: string
  structured_query: Record<string, unknown>
}

export type WorkflowState = {
  campaign_id: string
  run_id?: string | null
  status: string
  current_step: string
  steps: Array<Record<string, unknown>>
  jobs: Array<Record<string, unknown>>
  artifacts: Array<Record<string, unknown>>
  review_items: Array<Record<string, unknown>>
  activity: Array<Record<string, unknown>>
}

export type AuthToken = {
  access_token: string
  token_type: string
  user: { id: string; email: string; created_at: string }
}

const baseUrl = '/api'
const tokenKey = 'jobcopilot.token'

export class ApiError extends Error {
  status: number
  details: string

  constructor(status: number, details: string) {
    super(details)
    this.status = status
    this.details = details
  }
}

export function getToken() {
  return sessionStorage.getItem(tokenKey)
}

export function setToken(token: string) {
  sessionStorage.setItem(tokenKey, token)
}

export function clearToken() {
  sessionStorage.removeItem(tokenKey)
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const token = getToken()
  const response = await fetch(`${baseUrl}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init?.headers ?? {}),
    },
    ...init,
  })
  if (!response.ok) {
    throw new ApiError(response.status, await response.text())
  }
  return response.json() as Promise<T>
}

function mockId(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`
}

function mockNow() {
  return new Date().toISOString()
}

async function fallback<T>(task: Promise<T>, mockValue: T): Promise<T> {
  try {
    return await task
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    return mockValue
  }
}

export const api = {
  login: (username: string, password: string) =>
    fallback(
      request<AuthToken>('/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({ username, password }).toString(),
      }),
      {
        access_token: mockId('demo-token'),
        token_type: 'bearer',
        user: { id: mockId('user'), email: username || 'admin@jobcopilot.local', created_at: mockNow() },
      },
    ),
  health: () => fallback(request<{ status: string }>('/health'), { status: 'demo' }),
  databaseHealth: () =>
    fallback(request<{ status: string; database_url: string }>('/health/database'), {
      status: 'demo',
      database_url: 'demo',
    }),
  uploadResumeFile: (file: File) => {
    const form = new FormData()
    form.append('resume_file', file)
    return fallback(
      fetch(`${baseUrl}/career-vault/resume/upload`, {
        method: 'POST',
        headers: getToken() ? { Authorization: `Bearer ${getToken()}` } : {},
        body: form,
      }).then(async (response) => {
        if (!response.ok) throw new ApiError(response.status, await response.text())
        return response.json() as Promise<ResumeUploadResult>
      }),
      {
        status: 'success',
        upload_status: 'mocked',
        profile_id: mockId('profile'),
        filename: file.name,
        content_type: file.type || 'application/octet-stream',
        file_size: file.size,
        text_length: 0,
        created_at: new Date().toISOString(),
        server_saved: true,
        parsed_resume: {
          candidate_name: 'Sam Patel',
          email: 'sam.patel@example.com',
          phone: '+1 555 0100',
          location: 'Remote',
          summary: 'Demo parsed resume.',
          skills: ['FastAPI', 'Postgres', 'Docker'],
          experience: ['Built AI automation workflows for consulting clients.'],
          projects: [],
          education: [],
          certifications: [],
          approved_claims_boundary: ['Built AI automation workflows for consulting clients.'],
          missing_info: ['education'],
          parser_warnings: [],
          raw_json: {},
        },
        warnings: [],
        raw_response: {},
      },
    )
  },
  saveResumeText: (fileName: string, resumeText: string) =>
    fallback(
      fetch(`${baseUrl}/career-vault/resume/upload`, {
        method: 'POST',
        headers: getToken() ? { Authorization: `Bearer ${getToken()}` } : {},
        body: (() => {
          const form = new FormData()
          form.append('resume_text', resumeText)
          form.append('resume_filename', fileName)
          return form
        })(),
      }).then(async (response) => {
        if (!response.ok) throw new ApiError(response.status, await response.text())
        return response.json() as Promise<ResumeUploadResult>
      }),
      {
        status: 'success',
        upload_status: 'mocked',
        profile_id: mockId('profile'),
        filename: fileName,
        content_type: 'text/plain',
        file_size: resumeText.length,
        text_length: resumeText.length,
        created_at: new Date().toISOString(),
        server_saved: true,
        parsed_resume: {
          candidate_name: 'Sam Patel',
          email: 'sam.patel@example.com',
          phone: '+1 555 0100',
          location: 'Remote',
          summary: 'Demo parsed resume.',
          skills: ['FastAPI', 'Postgres', 'Docker'],
          experience: ['Built AI automation workflows for consulting clients.'],
          projects: [],
          education: [],
          certifications: [],
          approved_claims_boundary: ['Built AI automation workflows for consulting clients.'],
          missing_info: ['education'],
          parser_warnings: [],
          raw_json: {},
        },
        warnings: [],
        raw_response: {},
      },
    ),
  createCampaign: (payload: { natural_language_prompt: string; execution_mode: string; candidate_profile_id?: string }) =>
    fallback(
      request<CampaignCreate>('/campaigns/create', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
      {
        campaign_id: mockId('campaign'),
        campaign_name: 'Demo campaign',
        status: 'pending_review',
        structured_query: {
          prompt: payload.natural_language_prompt,
          execution_mode: payload.execution_mode,
          candidate_profile_id: payload.candidate_profile_id ?? null,
        },
      },
    ),
  runCampaign: (campaignId: string) =>
    fallback(
      request<{ run_id: string; workflow_run_id: string; status: string; current_step: string; campaign_id: string }>(
        `/campaigns/${campaignId}/run`,
        { method: 'POST' },
      ),
      { run_id: mockId('run'), workflow_run_id: mockId('run'), status: 'queued', current_step: 'job_discovery', campaign_id: campaignId },
    ),
  campaignStatus: (campaignId: string) =>
    fallback(request<WorkflowState>(`/campaigns/${campaignId}/status`), {
      campaign_id: campaignId,
      run_id: mockId('run'),
      status: 'pending_review',
      current_step: 'review_queue',
      steps: [],
      jobs: [],
      artifacts: [],
      review_items: [],
      activity: [],
    }),
  campaignJobs: (campaignId: string) =>
    fallback(request<Array<Record<string, unknown>>>(`/campaigns/${campaignId}/jobs`), [
      { id: mockId('job'), title: 'AI Consultant', company_name: 'Demo Corp', fit_score: 0.91, status: 'shortlisted' },
      { id: mockId('job'), title: 'Automation Engineer', company_name: 'Sample Systems', fit_score: 0.87, status: 'shortlisted' },
    ]),
  createGmailDraft: (outreachDraftId: string) =>
    fallback(
      request<{ outreach_draft_id: string; gmail_draft_id: string; gmail_draft_status: string; status: string }>(
        '/outreach-drafts/gmail-draft',
        {
          method: 'POST',
          body: JSON.stringify({ outreach_draft_id: outreachDraftId }),
      },
      ),
      {
        outreach_draft_id: outreachDraftId,
        gmail_draft_id: mockId('draft'),
        gmail_draft_status: 'draft_created',
        status: 'draft_created',
      },
    ),
  profileParsed: (profileId: string) =>
    fallback(request<Record<string, unknown>>(`/career-vault/profiles/${profileId}/parsed`), {
      candidate_name: 'Sam Patel',
      email: 'sam.patel@example.com',
      phone: '+1 555 0100',
      location: 'Remote',
      summary: 'Demo parsed resume.',
      skills: ['FastAPI', 'Postgres', 'Docker'],
      experience: ['Built AI automation workflows for consulting clients.'],
      projects: [],
      education: [],
      certifications: [],
      approved_claims_boundary: ['Built AI automation workflows for consulting clients.'],
      missing_info: ['education'],
      parser_warnings: [],
      raw_json: {},
    }),
  campaignArtifacts: (campaignId: string) =>
    fallback(request<Array<Record<string, unknown>>>(`/campaigns/${campaignId}/artifacts`), []),
  campaignReviewQueue: (campaignId: string) =>
    fallback(request<Array<Record<string, unknown>>>(`/campaigns/${campaignId}/review-queue`), []),
  campaignActivity: (campaignId: string) =>
    fallback(request<Array<Record<string, unknown>>>(`/campaigns/${campaignId}/activity`), []),
  manualJob: (campaignId: string, payload: Record<string, unknown>) =>
    fallback(
      request<Record<string, unknown>>(`/campaigns/${campaignId}/manual-job`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
      {
        campaign_id: campaignId,
        status: 'queued',
        reason: 'Manual job added because no external job source is configured',
        job: {
          job_id: mockId('job'),
          title: String(payload.role_title ?? 'Manual job'),
          company: String(payload.company_name ?? 'Manual company'),
        },
      },
    ),
  approveReview: (campaignId: string, reviewId: string) =>
    fallback(request<Record<string, unknown>>(`/campaigns/${campaignId}/review-queue/${reviewId}/approve`, { method: 'POST' }), {
      review_id: reviewId,
      status: 'approved',
    }),
  rejectReview: (campaignId: string, reviewId: string) =>
    fallback(request<Record<string, unknown>>(`/campaigns/${campaignId}/review-queue/${reviewId}/reject`, { method: 'POST' }), {
      review_id: reviewId,
      status: 'rejected',
    }),
}
