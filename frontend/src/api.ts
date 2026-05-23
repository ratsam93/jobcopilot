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
  parsed_campaign?: Record<string, unknown>
  execution_mode?: string
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
  jobs_discovered?: number
  zero_jobs_reason?: string
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

async function parseJsonResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    throw new ApiError(response.status, await response.text())
  }
  return response.json() as Promise<T>
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
  return parseJsonResponse<T>(response)
}

function authHeaders() {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export const api = {
  login: (username: string, password: string) =>
    request<AuthToken>('/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({ username, password }).toString(),
    }),
  health: () => request<{ status: string }>('/health'),
  databaseHealth: () => request<{ status: string; database_url: string }>('/health/database'),
  uploadResumeFile: (file: File) => {
    const form = new FormData()
    form.append('resume_file', file)
    return fetch(`${baseUrl}/career-vault/resume/upload`, {
      method: 'POST',
      headers: authHeaders(),
      body: form,
    }).then((response) => parseJsonResponse<ResumeUploadResult>(response))
  },
  saveResumeText: (fileName: string, resumeText: string) =>
    fetch(`${baseUrl}/career-vault/resume/upload`, {
      method: 'POST',
      headers: authHeaders(),
      body: (() => {
        const form = new FormData()
        form.append('resume_text', resumeText)
        form.append('resume_filename', fileName)
        return form
      })(),
    }).then((response) => parseJsonResponse<ResumeUploadResult>(response)),
  createCampaign: (payload: { natural_language_prompt: string; execution_mode: string; candidate_profile_id?: string }) =>
    request<CampaignCreate>('/campaigns/create', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  runCampaign: (campaignId: string) =>
    request<{ run_id: string; workflow_run_id: string; status: string; current_step: string; campaign_id: string }>(
      `/campaigns/${campaignId}/run`,
      { method: 'POST' },
    ),
  campaignStatus: (campaignId: string) => request<WorkflowState>(`/campaigns/${campaignId}/status`),
  campaignJobs: (campaignId: string) => request<Array<Record<string, unknown>>>(`/campaigns/${campaignId}/jobs`),
  createGmailDraft: (outreachDraftId: string) =>
    request<{ outreach_draft_id: string; gmail_draft_id: string; gmail_draft_status: string; status: string }>(
      '/outreach-drafts/gmail-draft',
      {
        method: 'POST',
        body: JSON.stringify({ outreach_draft_id: outreachDraftId }),
      },
    ),
  profileParsed: (profileId: string) => request<Record<string, unknown>>(`/career-vault/profiles/${profileId}/parsed`),
  campaignArtifacts: (campaignId: string) => request<Array<Record<string, unknown>>>(`/campaigns/${campaignId}/artifacts`),
  campaignReviewQueue: (campaignId: string) => request<Array<Record<string, unknown>>>(`/campaigns/${campaignId}/review-queue`),
  campaignActivity: (campaignId: string) => request<Array<Record<string, unknown>>>(`/campaigns/${campaignId}/activity`),
  manualJob: (campaignId: string, payload: Record<string, unknown>) =>
    request<Record<string, unknown>>(`/campaigns/${campaignId}/manual-job`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  approveReview: (campaignId: string, reviewId: string) =>
    request<Record<string, unknown>>(`/campaigns/${campaignId}/review-queue/${reviewId}/approve`, { method: 'POST' }),
  rejectReview: (campaignId: string, reviewId: string) =>
    request<Record<string, unknown>>(`/campaigns/${campaignId}/review-queue/${reviewId}/reject`, { method: 'POST' }),
}
