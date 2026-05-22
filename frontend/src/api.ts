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

const baseUrl = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    headers: {
      'Content-Type': 'application/json',
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
}

