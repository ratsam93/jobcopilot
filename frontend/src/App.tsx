import { useEffect, useMemo, useState } from 'react'
import { ApiError, api, clearToken, getToken, setToken } from './api'

type ActivityEvent = {
  timestamp: string
  action: string
  endpoint: string
  status: string
  entity_id: string
  message: string
  request?: unknown
  response?: unknown
  error?: string
}

type ResumeState = {
  profileId: string
  filename: string
  contentType: string
  fileSize: number
  textLength: number
  createdAt: string
  serverSaved: boolean
  parsed: Record<string, unknown> | null
  raw: Record<string, unknown> | null
}

type CampaignState = {
  campaignId: string
  campaignName: string
  approvalMode: string
  raw: Record<string, unknown> | null
}

type RunState = {
  runId: string
  status: string
  currentStep: string
  raw: Record<string, unknown> | null
}

const STORAGE = {
  token: 'jobcopilot.token',
  email: 'jobcopilot.userEmail',
  profileId: 'jobcopilot.profileId',
  campaignId: 'jobcopilot.campaignId',
  runId: 'jobcopilot.runId',
  approvalMode: 'jobcopilot.approvalMode',
}

const steps = [
  'Auth',
  'Resume Intake',
  'Resume Parse',
  'Campaign Create',
  'Job Discovery',
  'Fit Scoring',
  'Document Generation',
  'Outreach Drafting',
  'Review Queue',
  'Gmail Draft',
]

const defaultResume = `Sam Patel
AI Consultant

AI automation, FastAPI, SQL, Postgres, Docker, AWS, LLMs

- Built AI automation workflows for consulting clients.
- Led backend APIs using FastAPI and SQL.`

const defaultPrompt =
  'Apply to top technology companies across the USA where I am fit. Prepare resume, cover letter, find hiring manager and recruiter, but do not send anything without my approval.'

function now() {
  return new Date().toISOString()
}

function eventMessage(a: Partial<ActivityEvent> & Pick<ActivityEvent, 'action' | 'endpoint' | 'status' | 'message'>): ActivityEvent {
  return {
    timestamp: now(),
    entity_id: a.entity_id ?? '',
    request: a.request,
    response: a.response,
    error: a.error,
    action: a.action,
    endpoint: a.endpoint,
    status: a.status,
    message: a.message,
  }
}

export default function App() {
  const [token, setTokenState] = useState(getToken() ?? '')
  const [email, setEmail] = useState(sessionStorage.getItem(STORAGE.email) ?? 'admin@jobcopilot.local')
  const [password, setPassword] = useState('admin123')
  const [backendStatus, setBackendStatus] = useState('loading')
  const [databaseStatus, setDatabaseStatus] = useState('loading')
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [resumeText, setResumeText] = useState(defaultResume)
  const [resumeFileName, setResumeFileName] = useState('sample_resume_ai_consultant.txt')
  const [resumeState, setResumeState] = useState<ResumeState | null>(null)
  const [campaignPrompt, setCampaignPrompt] = useState(defaultPrompt)
  const [campaignState, setCampaignState] = useState<CampaignState | null>(null)
  const [runState, setRunState] = useState<RunState | null>(null)
  const [workflowState, setWorkflowState] = useState<Record<string, unknown> | null>(null)
  const [jobs, setJobs] = useState<Array<Record<string, unknown>>>([])
  const [artifacts, setArtifacts] = useState<Array<Record<string, unknown>>>([])
  const [reviewQueue, setReviewQueue] = useState<Array<Record<string, unknown>>>([])
  const [activity, setActivity] = useState<ActivityEvent[]>([])
  const [selectedArtifactTab, setSelectedArtifactTab] = useState<'resume' | 'cover' | 'recruiter' | 'hiring' | 'referral' | 'call' | 'raw'>('resume')
  const [selectedResumeTab, setSelectedResumeTab] = useState<'parsed' | 'raw'>('parsed')
  const [lastRequest, setLastRequest] = useState<unknown>(null)
  const [lastResponse, setLastResponse] = useState<unknown>(null)
  const [lastError, setLastError] = useState<string>('')
  const [manualJobTitle, setManualJobTitle] = useState('')
  const [manualJobCompany, setManualJobCompany] = useState('')
  const [manualJobDescription, setManualJobDescription] = useState('')
  const [manualJobSourceUrl, setManualJobSourceUrl] = useState('')
  const [gmailDraftId, setGmailDraftId] = useState('')
  const [loginBusy, setLoginBusy] = useState(false)
  const [isPolling, setIsPolling] = useState(false)
  const [activeStepIndex, setActiveStepIndex] = useState(0)
  const [stepInspector, setStepInspector] = useState<{ name: string; kind: 'input' | 'output' | 'error'; payload: unknown } | null>(null)

  const loggedIn = Boolean(token)
  const currentProfileId = resumeState?.profileId ?? sessionStorage.getItem(STORAGE.profileId) ?? ''
  const currentCampaignId = campaignState?.campaignId ?? sessionStorage.getItem(STORAGE.campaignId) ?? ''
  const currentRunId = runState?.runId ?? sessionStorage.getItem(STORAGE.runId) ?? ''
  const approvalMode = campaignState?.approvalMode ?? sessionStorage.getItem(STORAGE.approvalMode) ?? 'approval_required'

  const addActivity = (entry: ActivityEvent) => {
    setActivity((items) => {
      const prev = items[0]
      if (prev && prev.action === entry.action && prev.endpoint === entry.endpoint && prev.message === entry.message) {
        return items
      }
      return [entry, ...items].slice(0, 24)
    })
  }

  const apiCall = async <T,>(
    action: string,
    endpoint: string,
    fn: () => Promise<T>,
    request?: unknown,
    entityId = '',
  ): Promise<T> => {
    setLastRequest({ action, endpoint, request })
    try {
      const response = await fn()
      setLastResponse(response as unknown)
      setLastError('')
      addActivity(eventMessage({ action, endpoint, status: 'ok', entity_id: entityId, message: `${action} succeeded`, request, response }))
      return response
    } catch (error) {
      const message = error instanceof ApiError ? `HTTP ${error.status}: ${error.details}` : String(error)
      setLastError(message)
      setLastResponse(null)
      addActivity(eventMessage({ action, endpoint, status: 'failed', entity_id: entityId, message: `${action} failed`, request, error: message }))
      if (error instanceof ApiError && error.status === 401) {
        clearSession()
      }
      throw error
    }
  }

  const clearSession = () => {
    clearToken()
    sessionStorage.removeItem(STORAGE.email)
    sessionStorage.removeItem(STORAGE.profileId)
    sessionStorage.removeItem(STORAGE.campaignId)
    sessionStorage.removeItem(STORAGE.runId)
    sessionStorage.removeItem(STORAGE.approvalMode)
    setTokenState('')
  }

  const refreshHealth = async () => {
    const [app, db] = await Promise.all([api.health(), api.databaseHealth()])
    setBackendStatus(app.status)
    setDatabaseStatus(db.status)
  }

  const refreshWorkflow = async (campaignId: string) => {
    if (!campaignId) return
    const [state, jobsResponse, artifactsResponse, reviewResponse, activityResponse] = await Promise.all([
      api.campaignStatus(campaignId),
      api.campaignJobs(campaignId),
      api.campaignArtifacts(campaignId),
      api.campaignReviewQueue(campaignId),
      api.campaignActivity(campaignId),
    ])
    setWorkflowState(state)
    setRunState({
      runId: String(state.run_id ?? currentRunId ?? ''),
      status: String(state.status ?? 'not_started'),
      currentStep: String(state.current_step ?? 'not_started'),
      raw: state,
    })
    setJobs(jobsResponse)
    setArtifacts(artifactsResponse)
    setReviewQueue(reviewResponse)
    setActivity(
      activityResponse.map((item) =>
        eventMessage({
          action: String(item.event_type ?? 'activity'),
          endpoint: '/api/campaigns/activity',
          status: 'ok',
          entity_id: String(item.id ?? ''),
          message: String(item.event_type ?? 'event'),
          response: item,
        }),
      ),
    )
    if (state.steps && Array.isArray(state.steps)) {
      const activeIndex = state.steps.findIndex((step: Record<string, unknown>) => step.status === 'running')
      setActiveStepIndex(activeIndex >= 0 ? activeIndex : Math.max(0, state.steps.length - 1))
    }
  }

  const loadSnapshot = async () => {
    await refreshHealth()
    if (currentProfileId) {
      try {
        const parsed = await api.profileParsed(currentProfileId)
        setResumeState((previous) => ({
          profileId: currentProfileId,
          filename: previous?.filename ?? resumeFileName,
          contentType: previous?.contentType ?? 'text/plain',
          fileSize: previous?.fileSize ?? 0,
          textLength: previous?.textLength ?? 0,
          createdAt: previous?.createdAt ?? now(),
          serverSaved: true,
          parsed,
          raw: parsed,
        }))
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          clearSession()
          return
        }
        throw error
      }
    }
    if (currentCampaignId) {
      try {
        await refreshWorkflow(currentCampaignId)
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) {
          clearSession()
          return
        }
        throw error
      }
    }
  }

  useEffect(() => {
    void loadSnapshot()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (!runState || !['queued', 'running'].includes(runState.status)) return
    setIsPolling(true)
    const timer = window.setInterval(() => {
      void refreshWorkflow(currentCampaignId)
    }, 3000)
    return () => {
      window.clearInterval(timer)
      setIsPolling(false)
    }
  }, [currentCampaignId, runState])

  const handleLogin = async () => {
    setLoginBusy(true)
    try {
      const response = await apiCall('login', '/api/auth/login', () => api.login(email, password), { email }, 'auth')
      setToken(response.access_token)
      setTokenState(response.access_token)
      sessionStorage.setItem(STORAGE.email, response.user.email)
      setEmail(response.user.email)
      await loadSnapshot()
    } catch {
      // handled by apiCall
    } finally {
      setLoginBusy(false)
    }
  }

  const handleLogout = () => {
    clearSession()
    setResumeState(null)
    setCampaignState(null)
    setRunState(null)
    setWorkflowState(null)
    setJobs([])
    setArtifacts([])
    setReviewQueue([])
    setActivity([])
    setLastRequest(null)
    setLastResponse(null)
    setLastError('')
    addActivity(eventMessage({ action: 'logout', endpoint: '/api/auth/logout', status: 'ok', entity_id: '', message: 'Logged out' }))
  }

  const handleUploadResumeFile = async () => {
    if (!resumeFile) return
    const response = await apiCall('upload_resume', '/api/career-vault/resume/upload', () => api.uploadResumeFile(resumeFile), { filename: resumeFile.name, content_type: resumeFile.type, file_size: resumeFile.size }, 'resume')
    const parsed = response.parsed_resume
    setResumeState({
      profileId: response.profile_id,
      filename: response.filename,
      contentType: response.content_type ?? '',
      fileSize: response.file_size,
      textLength: response.text_length,
      createdAt: response.created_at,
      serverSaved: response.server_saved,
      parsed,
      raw: response.raw_response,
    })
    sessionStorage.setItem(STORAGE.profileId, response.profile_id)
    await loadSnapshot()
  }

  const handleSavePastedResume = async () => {
    const response = await apiCall(
      'save_pasted_resume',
      '/api/career-vault/resume/upload',
      () => api.saveResumeText(resumeFileName, resumeText),
      { filename: resumeFileName, text_length: resumeText.length },
      'resume',
    )
    setResumeState({
      profileId: response.profile_id,
      filename: response.filename,
      contentType: response.content_type ?? '',
      fileSize: response.file_size,
      textLength: response.text_length,
      createdAt: response.created_at,
      serverSaved: response.server_saved,
      parsed: response.parsed_resume,
      raw: response.raw_response,
    })
    sessionStorage.setItem(STORAGE.profileId, response.profile_id)
    await loadSnapshot()
  }

  const handleCreateCampaign = async () => {
    if (!currentProfileId) return
    const response = await apiCall(
      'create_campaign',
      '/api/campaigns/create',
      () =>
        api.createCampaign({
          natural_language_prompt: campaignPrompt,
          execution_mode: 'approval_required',
          candidate_profile_id: currentProfileId || undefined,
        }),
      { natural_language_prompt: campaignPrompt, candidate_profile_id: currentProfileId },
      'campaign',
    )
    const raw = response.parsed_campaign
    setCampaignState({
      campaignId: response.campaign_id,
      campaignName: String(raw.campaign_name ?? 'Campaign'),
      approvalMode: String(response.approval_mode),
      raw,
    })
    sessionStorage.setItem(STORAGE.campaignId, response.campaign_id)
    sessionStorage.setItem(STORAGE.approvalMode, String(response.approval_mode))
    await loadSnapshot()
  }

  const handleRunCampaign = async () => {
    if (!currentCampaignId) return
    const response = await apiCall(
      'run_campaign',
      `/api/campaigns/${currentCampaignId}/run`,
      () => api.runCampaign(currentCampaignId),
      { campaign_id: currentCampaignId },
      currentCampaignId,
    )
    setRunState({
      runId: response.run_id,
      status: response.status,
      currentStep: response.current_step,
      raw: response,
    })
    sessionStorage.setItem(STORAGE.runId, response.run_id)
    await loadSnapshot()
  }

  const handleManualJob = async () => {
    if (!currentCampaignId) return
    await apiCall(
      'manual_job',
      `/api/campaigns/${currentCampaignId}/manual-job`,
      () =>
        api.manualJob(currentCampaignId, {
          company_name: manualJobCompany,
          role_title: manualJobTitle,
          source: 'manual',
          source_url: manualJobSourceUrl,
          description: manualJobDescription,
        }),
      {
        company_name: manualJobCompany,
        role_title: manualJobTitle,
        source_url: manualJobSourceUrl,
      },
      currentCampaignId,
    )
    await loadSnapshot()
  }

  const handleApproveReview = async (reviewId: string) => {
    if (!currentCampaignId) return
    await apiCall('approve_review', `/api/campaigns/${currentCampaignId}/review-queue/${reviewId}/approve`, () => api.approveReview(currentCampaignId, reviewId), { review_id: reviewId }, reviewId)
    await loadSnapshot()
  }

  const handleRejectReview = async (reviewId: string) => {
    if (!currentCampaignId) return
    await apiCall('reject_review', `/api/campaigns/${currentCampaignId}/review-queue/${reviewId}/reject`, () => api.rejectReview(currentCampaignId, reviewId), { review_id: reviewId }, reviewId)
    await loadSnapshot()
  }

  const handleCreateGmailDraft = async () => {
    if (!gmailDraftId) return
    await apiCall('create_gmail_draft', '/api/outreach-drafts/gmail-draft', () => api.createGmailDraft(gmailDraftId), { outreach_draft_id: gmailDraftId }, gmailDraftId)
    await loadSnapshot()
  }

  const stepStates = useMemo(() => {
    const fromBackend = (workflowState?.steps as Array<Record<string, unknown>> | undefined) ?? []
    return steps.map((name, index) => {
      const backendStep = fromBackend[index]
      const status = String(backendStep?.status ?? (index === 0 && loggedIn ? 'complete' : 'not_started'))
      return {
        name,
        status,
        last_updated: String(backendStep?.completed_at ?? backendStep?.started_at ?? ''),
        input: backendStep?.input ?? {},
        output: backendStep?.output ?? {},
        error: backendStep?.error ?? null,
      }
    })
  }, [loggedIn, workflowState])

  const selectedResume = selectedResumeTab === 'parsed' ? resumeState?.parsed : resumeState?.raw
  const visibleArtifact = (() => {
    const target = selectedArtifactTab
    const mapping: Record<string, string | undefined> = {
      resume: 'resume',
      cover: 'cover_letter',
      recruiter: 'recruiter_email',
      hiring: 'hiring_manager_email',
      referral: 'referral_note',
      call: 'call_script',
      raw: undefined,
    }
    if (target === 'raw') return artifacts
    return artifacts.find((item) => String(item.type ?? item.artifact_type ?? '').includes(String(mapping[target] ?? '')))
  })()

  return (
    <main className="shell operator-shell">
      <section className="topbar">
        <div className="status-pill">Backend: {backendStatus}</div>
        <div className="status-pill">Database: {databaseStatus}</div>
        <div className="status-pill">Auth: {loggedIn ? 'signed_in' : 'signed_out'}</div>
        <div className="status-pill">User: {loggedIn ? email : 'not signed in'}</div>
        <div className="status-pill">Profile: {currentProfileId || 'none'}</div>
        <div className="status-pill">Campaign: {currentCampaignId || 'none'}</div>
        <div className="status-pill">Run: {currentRunId || 'none'}</div>
        <div className="status-pill">Approval: {approvalMode}</div>
      </section>

      <section className="console-grid">
        <aside className="column panel">
          <h2>Workflow Stepper</h2>
          <div className="stepper">
            {stepStates.map((step, index) => (
              <div key={step.name} className={`step ${activeStepIndex === index ? 'active' : ''}`}>
                <div className="step-head">
                  <strong>{step.name}</strong>
                  <span className={`step-status ${step.status}`}>{step.status}</span>
                </div>
                <small>{step.last_updated || 'not updated'}</small>
                <div className="step-links">
                  <button type="button" className="ghost" onClick={() => setStepInspector({ name: step.name, kind: 'input', payload: step.input })}>view input</button>
                  <button type="button" className="ghost" onClick={() => setStepInspector({ name: step.name, kind: 'output', payload: step.output })}>view output</button>
                  <button type="button" className="ghost" onClick={() => setStepInspector({ name: step.name, kind: 'error', payload: step.error })}>view error</button>
                </div>
              </div>
            ))}
          </div>
        </aside>

        <section className="column content-column">
          <section className="panel">
            <div className="panel-head">
              <h2>Auth</h2>
              {loggedIn && <button className="secondary" onClick={handleLogout}>Logout</button>}
            </div>
            <div className="grid-2">
              <label>
                Email
                <input value={email} onChange={(e) => setEmail(e.target.value)} />
              </label>
              <label>
                Password
                <input value={password} type="password" onChange={(e) => setPassword(e.target.value)} />
              </label>
            </div>
            <button onClick={handleLogin} disabled={loginBusy}>{loginBusy ? 'Logging in...' : 'Log in'}</button>
            <div className="meta">Session token: {token ? 'present' : 'not set'}</div>
          </section>

          <section className="panel">
            <div className="panel-head">
              <h2>Resume Intake</h2>
              <span className="meta">Upload real file or paste text</span>
            </div>
            <div className="grid-2">
              <label>
                Resume file
                <input type="file" accept=".pdf,.docx,.txt" onChange={(e) => setResumeFile(e.target.files?.[0] ?? null)} />
              </label>
              <label>
                File name
                <input value={resumeFileName} onChange={(e) => setResumeFileName(e.target.value)} />
              </label>
            </div>
            <label>
              Pasted resume text
              <textarea rows={8} value={resumeText} onChange={(e) => setResumeText(e.target.value)} />
            </label>
            <div className="button-row">
              <button onClick={handleUploadResumeFile} disabled={!resumeFile}>Upload Resume File</button>
              <button onClick={handleSavePastedResume}>Save Pasted Resume</button>
            </div>
            {resumeState && (
              <div className="summary-strip">
                <span>upload_status: {resumeState.parsed ? 'success' : 'pending'}</span>
                <span>profile_id: {resumeState.profileId}</span>
                <span>filename: {resumeState.filename}</span>
                <span>content_type: {resumeState.contentType}</span>
                <span>file_size: {resumeState.fileSize}</span>
                <span>text_length: {resumeState.textLength}</span>
                <span>created_at: {resumeState.createdAt}</span>
                <span>server_saved: {String(resumeState.serverSaved)}</span>
              </div>
            )}
            <details>
              <summary>API Response</summary>
              <pre className="json">{JSON.stringify(lastResponse, null, 2)}</pre>
            </details>
          </section>

          <section className="panel">
            <div className="panel-head">
              <h2>Resume Parse Output</h2>
              <div className="tab-row">
                <button className={selectedResumeTab === 'parsed' ? '' : 'secondary'} onClick={() => setSelectedResumeTab('parsed')}>Parsed</button>
                <button className={selectedResumeTab === 'raw' ? '' : 'secondary'} onClick={() => setSelectedResumeTab('raw')}>Raw JSON</button>
              </div>
            </div>
            <div className="parsed-grid">
              <Field label="Candidate name" value={String(selectedResume?.candidate_name ?? '')} />
              <Field label="Email" value={String(selectedResume?.email ?? '')} />
              <Field label="Phone" value={String(selectedResume?.phone ?? '')} />
              <Field label="Location" value={String(selectedResume?.location ?? '')} />
              <Field label="Summary" value={String(selectedResume?.summary ?? '')} />
              <Field label="Skills" value={Array.isArray(selectedResume?.skills) ? (selectedResume?.skills as string[]).join(', ') : ''} />
              <Field label="Experience" value={Array.isArray(selectedResume?.experience) ? (selectedResume?.experience as string[]).join(' | ') : ''} />
              <Field label="Projects" value={Array.isArray(selectedResume?.projects) ? (selectedResume?.projects as string[]).join(' | ') : ''} />
              <Field label="Education" value={Array.isArray(selectedResume?.education) ? (selectedResume?.education as string[]).join(' | ') : ''} />
              <Field label="Certifications" value={Array.isArray(selectedResume?.certifications) ? (selectedResume?.certifications as string[]).join(' | ') : ''} />
              <Field label="Approved claims boundary" value={Array.isArray(selectedResume?.approved_claims_boundary) ? (selectedResume?.approved_claims_boundary as string[]).join(' | ') : ''} />
              <Field label="Missing info" value={Array.isArray(selectedResume?.missing_info) ? (selectedResume?.missing_info as string[]).join(', ') : ''} />
              <Field label="Parser warnings" value={Array.isArray(selectedResume?.parser_warnings) ? (selectedResume?.parser_warnings as string[]).join(', ') : ''} />
            </div>
            <details>
              <summary>Raw JSON</summary>
              <pre className="json">{JSON.stringify(selectedResume, null, 2)}</pre>
            </details>
          </section>

          <section className="panel">
            <div className="panel-head">
              <h2>Campaign Planner</h2>
              <span className="meta">Create parsed campaign JSON before running workflow</span>
            </div>
            <label>
              Campaign prompt
              <textarea rows={6} value={campaignPrompt} onChange={(e) => setCampaignPrompt(e.target.value)} />
            </label>
            <div className="button-row">
              <button onClick={handleCreateCampaign} disabled={!currentProfileId}>Create Campaign</button>
              <button onClick={handleRunCampaign} disabled={!currentCampaignId}>Run Campaign</button>
            </div>
            {campaignState && (
              <div className="summary-strip">
                <span>campaign_id: {campaignState.campaignId}</span>
                <span>campaign_name: {campaignState.campaignName}</span>
                <span>approval_mode: {campaignState.approvalMode}</span>
              </div>
            )}
            <details>
              <summary>Raw request</summary>
              <pre className="json">{JSON.stringify(lastRequest, null, 2)}</pre>
            </details>
            <details>
              <summary>Raw response</summary>
              <pre className="json">{JSON.stringify(campaignState?.raw ?? lastResponse, null, 2)}</pre>
            </details>
          </section>

          <section className="panel">
            <div className="panel-head">
              <h2>Run State</h2>
              <span className={`step-status ${runState?.status ?? 'not_started'}`}>{runState?.status ?? 'not_started'}</span>
            </div>
            <div className="summary-strip">
              <span>run_id: {runState?.runId || 'none'}</span>
              <span>campaign_id: {currentCampaignId || 'none'}</span>
              <span>current_step: {runState?.currentStep || 'not_started'}</span>
              <span>queued_at: {String((workflowState as { queued_at?: string } | null)?.queued_at ?? '')}</span>
              <span>started_at: {String((workflowState as { started_at?: string } | null)?.started_at ?? '')}</span>
              <span>completed_at: {String((workflowState as { completed_at?: string } | null)?.completed_at ?? '')}</span>
              <span>error: {String((workflowState as { error?: string } | null)?.error ?? '')}</span>
            </div>
            <div className="meta">{isPolling ? 'Polling every 3 seconds while active' : 'Polling idle'}</div>
            <pre className="json">{JSON.stringify(workflowState, null, 2)}</pre>
          </section>

          <section className="panel">
            <div className="panel-head">
              <h2>Manual Job Flow</h2>
              <span className="meta">Use this when external job sources are not connected</span>
            </div>
            <div className="grid-2">
              <label>
                Company
                <input value={manualJobCompany} onChange={(e) => setManualJobCompany(e.target.value)} />
              </label>
              <label>
                Role title
                <input value={manualJobTitle} onChange={(e) => setManualJobTitle(e.target.value)} />
              </label>
            </div>
            <label>
              Job description
              <textarea rows={4} value={manualJobDescription} onChange={(e) => setManualJobDescription(e.target.value)} />
            </label>
            <label>
              Source URL
              <input value={manualJobSourceUrl} onChange={(e) => setManualJobSourceUrl(e.target.value)} />
            </label>
            <button onClick={handleManualJob} disabled={!currentCampaignId || !manualJobTitle || !manualJobCompany}>Add Manual Job</button>
          </section>

          <section className="panel">
            <div className="panel-head">
              <h2>Jobs Panel</h2>
              <span className="meta">{jobs.length === 0 ? 'No jobs discovered because no external job source is currently configured' : `${jobs.length} jobs`}</span>
            </div>
            <table className="table">
              <thead>
                <tr>
                  <th>company</th>
                  <th>role_title</th>
                  <th>source</th>
                  <th>location</th>
                  <th>remote</th>
                  <th>fit_score</th>
                  <th>status</th>
                  <th>reason</th>
                </tr>
              </thead>
              <tbody>
                {jobs.map((job, index) => (
                  <tr key={`${String(job.job_id ?? index)}`}>
                    <td>{String(job.company_name ?? job.company ?? '')}</td>
                    <td>{String(job.title ?? job.role_title ?? '')}</td>
                    <td>{String(job.source ?? '')}</td>
                    <td>{String(job.location ?? '')}</td>
                    <td>{String(job.remote ?? '')}</td>
                    <td>{String(job.fit_score ?? job.score ?? '')}</td>
                    <td>{String(job.status ?? '')}</td>
                    <td>{String(job.reason ?? job.explanation ?? '')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="panel">
            <div className="panel-head">
              <h2>Generated Artifacts</h2>
              <div className="tab-row">
                <button className={selectedArtifactTab === 'resume' ? '' : 'secondary'} onClick={() => setSelectedArtifactTab('resume')}>Tailored Resume</button>
                <button className={selectedArtifactTab === 'cover' ? '' : 'secondary'} onClick={() => setSelectedArtifactTab('cover')}>Cover Letter</button>
                <button className={selectedArtifactTab === 'recruiter' ? '' : 'secondary'} onClick={() => setSelectedArtifactTab('recruiter')}>Recruiter Email</button>
                <button className={selectedArtifactTab === 'hiring' ? '' : 'secondary'} onClick={() => setSelectedArtifactTab('hiring')}>Hiring Manager Email</button>
                <button className={selectedArtifactTab === 'referral' ? '' : 'secondary'} onClick={() => setSelectedArtifactTab('referral')}>Referral Note</button>
                <button className={selectedArtifactTab === 'call' ? '' : 'secondary'} onClick={() => setSelectedArtifactTab('call')}>Call Script</button>
                <button className={selectedArtifactTab === 'raw' ? '' : 'secondary'} onClick={() => setSelectedArtifactTab('raw')}>Raw JSON</button>
              </div>
            </div>
            {visibleArtifact ? (
              <div className="artifact-view">
                <div className="summary-strip">
                  <span>artifact_id: {String(visibleArtifact.application_package_id ?? visibleArtifact.review_id ?? visibleArtifact.outreach_draft_id ?? '')}</span>
                  <span>type: {String(visibleArtifact.type ?? visibleArtifact.artifact_type ?? visibleArtifact.draft_type ?? selectedArtifactTab)}</span>
                  <span>status: {String(visibleArtifact.status ?? '')}</span>
                  <span>created_at: {String(visibleArtifact.created_at ?? '')}</span>
                </div>
                <pre className="json">{JSON.stringify(visibleArtifact, null, 2)}</pre>
                <div className="button-row">
                  <button onClick={() => navigator.clipboard.writeText(JSON.stringify(visibleArtifact, null, 2))}>Copy</button>
                  <button onClick={() => setLastResponse(visibleArtifact)}>Download</button>
                  <button>Approve</button>
                  <button className="secondary">Reject</button>
                </div>
              </div>
            ) : (
              <div className="meta">No artifact selected or none generated yet.</div>
            )}
          </section>

          <section className="panel">
            <div className="panel-head">
              <h2>Review Queue</h2>
              <span className="meta">Nothing goes to Gmail draft unless status is approved</span>
            </div>
            <table className="table">
              <thead>
                <tr>
                  <th>review_item_id</th>
                  <th>artifact_type</th>
                  <th>company</th>
                  <th>role</th>
                  <th>status</th>
                  <th>preview</th>
                  <th>approve</th>
                  <th>reject</th>
                </tr>
              </thead>
              <tbody>
                {reviewQueue.map((item, index) => (
                  <tr key={`${String(item.review_id ?? index)}`}>
                    <td>{String(item.review_id ?? '')}</td>
                    <td>{String(item.entity_type ?? item.artifact_type ?? '')}</td>
                    <td>{String(item.company ?? '')}</td>
                    <td>{String(item.role ?? '')}</td>
                    <td>{String(item.status ?? '')}</td>
                    <td className="preview">{String(item.preview ?? item.review_notes ?? '').slice(0, 120)}</td>
                    <td><button onClick={() => handleApproveReview(String(item.review_id))}>Approve</button></td>
                    <td><button className="secondary" onClick={() => handleRejectReview(String(item.review_id))}>Reject</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          <section className="panel">
            <div className="panel-head">
              <h2>Gmail Draft</h2>
              <span className="meta">Approve an outreach draft first.</span>
            </div>
            <label>
              Outreach draft ID
              <input value={gmailDraftId} onChange={(e) => setGmailDraftId(e.target.value)} />
            </label>
            <button onClick={handleCreateGmailDraft} disabled={!gmailDraftId}>Create Gmail Draft</button>
            <pre className="json">{JSON.stringify(lastResponse, null, 2)}</pre>
          </section>
        </section>

        <aside className="column panel">
          <h2>Live Activity / Debug / Output</h2>
          <div className="meta">Backend base URL: /api</div>
          <div className="meta">Token present: {String(Boolean(token))}</div>
          <div className="meta">Frontend build version: local</div>
          <details open>
            <summary>Last API request</summary>
            <pre className="json">{JSON.stringify(lastRequest, null, 2)}</pre>
          </details>
          <details open>
            <summary>Last API response</summary>
            <pre className="json">{JSON.stringify(lastResponse, null, 2)}</pre>
          </details>
          <details open>
            <summary>Last error</summary>
            <pre className="json">{lastError || 'none'}</pre>
          </details>
          <details open>
            <summary>Activity log</summary>
            <button className="secondary" onClick={() => setActivity([])}>Clear Log</button>
            <div className="activity-list">
              {activity.map((entry, index) => (
                <article key={`${entry.timestamp}-${index}`} className="activity-item">
                  <div>{entry.timestamp}</div>
                  <div>{entry.action}</div>
                  <div>{entry.endpoint}</div>
                  <div>{entry.status}</div>
                  <div>{entry.entity_id}</div>
                  <div>{entry.message}</div>
                </article>
              ))}
            </div>
          </details>
          <details open>
            <summary>Workflow raw state</summary>
            <pre className="json">{JSON.stringify(workflowState, null, 2)}</pre>
          </details>
          <details open>
            <summary>Step inspector</summary>
            <div className="meta">{stepInspector ? `${stepInspector.name} / ${stepInspector.kind}` : 'Click a step view button to inspect input, output, or error.'}</div>
            <pre className="json">{JSON.stringify(stepInspector?.payload ?? null, null, 2)}</pre>
          </details>
        </aside>
      </section>
    </main>
  )
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div className="field-card">
      <span>{label}</span>
      <strong>{value || '—'}</strong>
    </div>
  )
}
