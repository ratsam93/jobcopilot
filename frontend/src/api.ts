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
  uploadResume: (fileName: string, content: string) =>
    request<CareerVaultUpload>('/career-vault/resume/upload', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/octet-stream',
        'X-Filename': fileName,
      },
      body: content,
    }),
  createCampaign: (payload: { natural_language_prompt: string; execution_mode: string; candidate_profile_id?: string }) =>
    request<CampaignCreate>('/campaigns/create', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  runCampaign: (campaignId: string) => request<{ status: string }>(`/campaigns/${campaignId}/run`, { method: 'POST' }),
  campaignStatus: (campaignId: string) => request<Record<string, unknown>>(`/campaigns/${campaignId}/status`),
  campaignJobs: (campaignId: string) => request<Array<Record<string, unknown>>>(`/campaigns/${campaignId}/jobs`),
  createGmailDraft: (outreachDraftId: string) =>
    request<{ outreach_draft_id: string; gmail_draft_id: string; gmail_draft_status: string; status: string }>(
      '/outreach-drafts/gmail-draft',
      {
        method: 'POST',
        body: JSON.stringify({ outreach_draft_id: outreachDraftId }),
      },
    ),
}
