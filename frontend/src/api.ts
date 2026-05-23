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

export type CampaignCreate = {
  campaign_id: string
  campaign_name: string
  status: string
  structured_query: Record<string, unknown>
}

export type AuthToken = {
  access_token: string
  token_type: string
  user: { id: string; email: string; created_at: string }
}

const baseUrl = '/api'
const tokenKey = 'jobcopilot.token'

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
    throw new Error(await response.text())
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
  } catch {
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
  uploadResume: (fileName: string, content: string) =>
    fallback(
      request<CareerVaultUpload>('/career-vault/resume/upload', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/octet-stream',
          'X-Filename': fileName,
        },
        body: content,
      }),
      {
        parse_status: 'mocked',
        source_filename: fileName,
        candidate_profile_id: mockId('profile'),
        created_profile: {
          full_name: 'Sam Patel',
          primary_email: 'sam.patel@example.com',
          target_roles: ['AI Consultant', 'Automation Engineer'],
          skills: [
            { skill_name: 'FastAPI' },
            { skill_name: 'Postgres' },
            { skill_name: 'Docker' },
          ],
          approved_claims: [
            { claim_text: 'Built AI automation workflows for consulting clients.' },
            { claim_text: 'Led backend APIs using FastAPI and SQL.' },
          ],
        },
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
    fallback(request<{ status: string }>(`/campaigns/${campaignId}/run`, { method: 'POST' }), { status: 'queued' }),
  campaignStatus: (campaignId: string) =>
    fallback(request<Record<string, unknown>>(`/campaigns/${campaignId}/status`), {
      campaign_id: campaignId,
      status: 'pending_review',
      execution_mode: 'approval_required',
      jobs_discovered: 3,
      application_packages_created: 1,
      people_search_completed: true,
      outreach_drafts_created: true,
      emails_sent: 0,
      applications_submitted: 0,
      approval_required: true,
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
}
