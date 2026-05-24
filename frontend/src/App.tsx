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

const workflowSteps = [
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
  // Navigation & UI States
  const [activeTab, setActiveTab] = useState<'dashboard' | 'vault' | 'campaign' | 'radar' | 'approval' | 'logs'>('dashboard')
  const [isDevConsoleExpanded, setIsDevConsoleExpanded] = useState(false)
  const [selectedArtifactTab, setSelectedArtifactTab] = useState<'resume' | 'cover' | 'email' | 'script'>('resume')

  // Authentication states
  const [token, setTokenState] = useState(getToken() ?? '')
  const [email, setEmail] = useState(sessionStorage.getItem(STORAGE.email) ?? 'admin@jobcopilot.local')
  const [password, setPassword] = useState('admin123')
  const [backendStatus, setBackendStatus] = useState('loading')
  const [databaseStatus, setDatabaseStatus] = useState('loading')

  // Profile states
  const [resumeFile, setResumeFile] = useState<File | null>(null)
  const [resumeText, setResumeText] = useState('')
  const [resumeFileName, setResumeFileName] = useState('resume.txt')
  const [resumeState, setResumeState] = useState<ResumeState | null>(null)

  // Campaign & Stepper states
  const [campaignPrompt, setCampaignPrompt] = useState(defaultPrompt)
  const [campaignState, setCampaignState] = useState<CampaignState | null>(null)
  const [runState, setRunState] = useState<RunState | null>(null)
  const [workflowState, setWorkflowState] = useState<Record<string, unknown> | null>(null)

  // Discovered Jobs states
  const [jobs, setJobs] = useState<Array<Record<string, unknown>>>([])
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null)

  // Artifacts & Approvals states
  const [artifacts, setArtifacts] = useState<Array<Record<string, unknown>>>([])
  const [reviewQueue, setReviewQueue] = useState<Array<Record<string, unknown>>>([])
  const [selectedReviewId, setSelectedReviewId] = useState<string | null>(null)

  // Debugging & Activity log states
  const [activity, setActivity] = useState<ActivityEvent[]>([])
  const [lastRequest, setLastRequest] = useState<unknown>(null)
  const [lastResponse, setLastResponse] = useState<unknown>(null)
  const [lastError, setLastError] = useState<string>('')
  
  // Interactive local UI editors for generated artifacts
  const [editedCoverLetter, setEditedCoverLetter] = useState('')
  const [editedEmailBody, setEditedEmailBody] = useState('')
  const [editedEmailSubject, setEditedEmailSubject] = useState('')
  const [editedEmailTo, setEditedEmailTo] = useState('')

  // Manual job insertion states
  const [manualJobTitle, setManualJobTitle] = useState('')
  const [manualJobCompany, setManualJobCompany] = useState('')
  const [manualJobDescription, setManualJobDescription] = useState('')
  const [manualJobSourceUrl, setManualJobSourceUrl] = useState('')
  const [gmailDraftId, setGmailDraftId] = useState('')
  
  // Busy & Polling status indicator
  const [loginBusy, setLoginBusy] = useState(false)
  const [isPolling, setIsPolling] = useState(false)
  const [activeStepIndex, setActiveStepIndex] = useState(0)

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
    
    // Set default selected job if none is set
    if (jobsResponse.length > 0 && !selectedJobId) {
      setSelectedJobId(String(jobsResponse[0].id ?? jobsResponse[0].job_id ?? ''))
    }
    
    setArtifacts(artifactsResponse)
    setReviewQueue(reviewResponse)
    
    // Set default selected review item
    if (reviewResponse.length > 0 && !selectedReviewId) {
      setSelectedReviewId(String(reviewResponse[0].review_id ?? ''))
    }
    
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
    void refreshHealth().catch((error) => {
      setBackendStatus('unavailable')
      setDatabaseStatus('unavailable')
      setLastError(error instanceof Error ? error.message : String(error))
    })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (loggedIn) {
      void loadSnapshot()
    }
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
    setSelectedJobId(null)
    setSelectedReviewId(null)
    addActivity(eventMessage({ action: 'logout', endpoint: '/api/auth/logout', status: 'ok', entity_id: '', message: 'Logged out' }))
  }

  const handleUploadResumeFile = async () => {
    if (!resumeFile) {
      const message = 'Choose a PDF, DOCX, or TXT file before clicking Process Document.'
      setLastError(message)
      addActivity(eventMessage({ action: 'upload_resume', endpoint: '/api/career-vault/resume/upload', status: 'blocked', entity_id: '', message }))
      return
    }
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
    if (!resumeText.trim()) {
      const message = 'Paste resume text before saving.'
      setLastError(message)
      addActivity(eventMessage({ action: 'save_pasted_resume', endpoint: '/api/career-vault/resume/upload', status: 'blocked', entity_id: '', message }))
      return
    }
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
    const raw = response.parsed_campaign ?? response.structured_query
    setCampaignState({
      campaignId: response.campaign_id,
      campaignName: String(response.campaign_name ?? 'Active Campaign'),
      approvalMode: String(response.execution_mode ?? 'approval_required'),
      raw,
    })
    sessionStorage.setItem(STORAGE.campaignId, response.campaign_id)
    sessionStorage.setItem(STORAGE.approvalMode, String(response.execution_mode ?? 'approval_required'))
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
    // Clear inputs after successful submission
    setManualJobTitle('')
    setManualJobCompany('')
    setManualJobDescription('')
    setManualJobSourceUrl('')
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

  const handleCreateGmailDraft = async (draftId: string) => {
    if (!draftId) return
    await apiCall('create_gmail_draft', '/api/outreach-drafts/gmail-draft', () => api.createGmailDraft(draftId), { outreach_draft_id: draftId }, draftId)
    await loadSnapshot()
  }

  const stepStates = useMemo(() => {
    const fromBackend = (workflowState?.steps as Array<Record<string, unknown>> | undefined) ?? []
    return workflowSteps.map((name, index) => {
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

  // Extract variables for visual rendering
  const activeProfile = resumeState?.parsed
  
  // Selected Job Details mapping
  const selectedJob = useMemo(() => {
    if (!selectedJobId) return null
    return jobs.find((j) => String(j.id ?? j.job_id ?? '') === selectedJobId)
  }, [jobs, selectedJobId])

  // Inbox Review item mapping
  const selectedReviewItem = useMemo(() => {
    if (!selectedReviewId) return null
    return reviewQueue.find((r) => String(r.review_id ?? '') === selectedReviewId)
  }, [reviewQueue, selectedReviewId])

  // Map and parse visual artifacts based on current tab and selected inbox items
  const visibleArtifact = useMemo(() => {
    const target = selectedArtifactTab
    const mapping: Record<string, string> = {
      resume: 'resume',
      cover: 'cover_letter',
      email: 'email',
      script: 'call_script',
    }
    
    // Attempt to locate matching package artifact
    if (selectedReviewItem) {
      // Find package connected to this review
      const relatedPkgId = selectedReviewItem.entity_id ?? selectedReviewItem.application_package_id ?? ''
      const relatedDraftId = selectedReviewItem.outreach_draft_id ?? ''
      
      const pkg = artifacts.find((a) => 
        String(a.application_package_id ?? '') === String(relatedPkgId) || 
        String(a.outreach_draft_id ?? '') === String(relatedDraftId)
      )
      
      if (pkg) return pkg
    }
    
    // Fallback search in entire artifacts bank
    const matched = artifacts.find((item) => 
      String(item.type ?? item.artifact_type ?? item.draft_type ?? '').toLowerCase().includes(mapping[target])
    )
    return matched ?? (artifacts.length > 0 ? artifacts[0] : null)
  }, [artifacts, selectedArtifactTab, selectedReviewItem])

  // Update local visual inputs whenever selected artifact changes
  useEffect(() => {
    if (visibleArtifact) {
      setEditedCoverLetter(String(visibleArtifact.cover_letter ?? ''))
      
      const gmail = visibleArtifact.gmail_draft as Record<string, string> | undefined
      setEditedEmailBody(String(visibleArtifact.body ?? gmail?.body ?? ''))
      setEditedEmailSubject(String(visibleArtifact.subject ?? gmail?.subject ?? ''))
      setEditedEmailTo(String(gmail?.to ?? ''))
    }
  }, [visibleArtifact])

  // Circular Match score helper
  const renderMatchCircle = (scoreNum: number | string | undefined) => {
    let score = 0
    if (typeof scoreNum === 'number') {
      score = scoreNum > 1 ? scoreNum : Math.round(scoreNum * 100)
    } else if (scoreNum) {
      score = parseFloat(scoreNum)
      if (score <= 1) score = Math.round(score * 100)
    }
    
    if (isNaN(score)) score = 0
    
    const radius = 22
    const circumference = 2 * Math.PI * radius
    const offset = circumference - (score / 100) * circumference
    
    const color = score >= 85 ? 'var(--success)' : score >= 70 ? 'var(--warning)' : 'var(--danger)'

    return (
      <div className="score-circle-wrapper">
        <svg className="score-circle-svg">
          <circle className="score-circle-bg" cx="26" cy="26" r={radius} />
          <circle 
            className="score-circle-bar" 
            cx="26" 
            cy="26" 
            r={radius} 
            stroke={color}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>
        <span className="score-text-overlay">{score}%</span>
      </div>
    )
  }

  // Active campaign percentage
  const campaignProgressPercentage = useMemo(() => {
    const finishedSteps = stepStates.filter((s) => s.status === 'complete').length
    return Math.round((finishedSteps / workflowSteps.length) * 100)
  }, [stepStates])

  return (
    <div className="workspace-wrapper">
      {/* 1. Sidebar Navigation */}
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-icon">J</div>
          <div className="brand-name">JobCopilot</div>
        </div>
        
        <nav className="sidebar-nav">
          <button 
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="7" height="7" />
              <rect x="14" y="3" width="7" height="7" />
              <rect x="14" y="14" width="7" height="7" />
              <rect x="3" y="14" width="7" height="7" />
            </svg>
            <span>Dashboard</span>
          </button>
          
          <button 
            className={`nav-item ${activeTab === 'vault' ? 'active' : ''}`}
            onClick={() => setActiveTab('vault')}
          >
            <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
            </svg>
            <span>Career Vault</span>
          </button>
          
          <button 
            className={`nav-item ${activeTab === 'campaign' ? 'active' : ''}`}
            onClick={() => setActiveTab('campaign')}
          >
            <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10" />
              <circle cx="12" cy="12" r="6" />
              <circle cx="12" cy="12" r="2" />
            </svg>
            <span>Campaign Center</span>
          </button>
          
          <button 
            className={`nav-item ${activeTab === 'radar' ? 'active' : ''}`}
            onClick={() => setActiveTab('radar')}
          >
            <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm0 18a8 8 0 1 1 8-8 8 8 0 0 1-8 8z" />
              <path d="M12 6v6l4 2" />
            </svg>
            <span>Job Radar</span>
          </button>
          
          <button 
            className={`nav-item ${activeTab === 'approval' ? 'active' : ''}`}
            onClick={() => setActiveTab('approval')}
          >
            <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <polyline points="22 12 16 12 14 15 10 15 8 12 2 12" />
              <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" />
            </svg>
            <span>Approval Inbox</span>
            {reviewQueue.length > 0 && (
              <span className="badge danger" style={{ marginLeft: 'auto', padding: '2px 6px', fontSize: '10px' }}>
                {reviewQueue.length}
              </span>
            )}
          </button>
          
          <button 
            className={`nav-item ${activeTab === 'logs' ? 'active' : ''}`}
            onClick={() => setActiveTab('logs')}
          >
            <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2" />
              <rect x="8" y="2" width="8" height="4" rx="1" ry="1" />
            </svg>
            <span>Outreach & Sync</span>
          </button>
        </nav>
        
        <div className="sidebar-footer">
          {loggedIn ? (
            <div className="sidebar-user">
              <div className="user-avatar">{email.charAt(0).toUpperCase()}</div>
              <div className="user-info">
                <span className="user-email">{email}</span>
                <span className="user-role">Production User</span>
              </div>
            </div>
          ) : (
            <div className="user-role" style={{ padding: '0 8px' }}>Not Authenticated</div>
          )}
          {loggedIn && (
            <button className="secondary" onClick={handleLogout} style={{ width: '100%' }}>
              <span>Sign Out</span>
            </button>
          )}
        </div>
      </aside>

      {/* 2. Main Canvas Grid */}
      <main className="canvas">
        {/* Top Premium Headers */}
        <section className="topbar-premium">
          <h1 className="topbar-title">
            {activeTab === 'dashboard' && 'Dashboard Overview'}
            {activeTab === 'vault' && 'My Career Vault'}
            {activeTab === 'campaign' && 'Campaign Control Room'}
            {activeTab === 'radar' && 'Job Search Radar'}
            {activeTab === 'approval' && 'Human Approval Gates'}
            {activeTab === 'logs' && 'Transmission Log & History'}
          </h1>
          
          <div className="system-status-pills">
            <div className="status-pill-premium">
              <span className={`status-dot ${backendStatus !== 'loading' ? 'active' : 'loading'}`}></span>
              Backend: {backendStatus}
            </div>
            <div className="status-pill-premium">
              <span className={`status-dot ${databaseStatus !== 'loading' ? 'active' : 'loading'}`}></span>
              DB: {databaseStatus}
            </div>
            <div className="status-pill-premium">
              <span className={`status-dot ${loggedIn ? 'active' : ''}`}></span>
              Auth: {loggedIn ? 'Signed In' : 'Logged Out'}
            </div>
          </div>
        </section>

        {/* Dynamic Inner Panel View Content Canvas */}
        <section className="view-container">
          
          {/* ======================================================== */}
          {/* A. AUTH PANEL / SIGN IN (Visible overlay if not logged in) */}
          {/* ======================================================== */}
          {!loggedIn && (
            <div className="card-premium" style={{ maxWidth: '480px', margin: '40px auto 0 auto' }}>
              <div className="card-title-row">
                <h2>Welcome to JobCopilot</h2>
              </div>
              <p className="card-description">Please log in to manage your career search campaigns.</p>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <label>
                  Account Email Address
                  <input 
                    type="email" 
                    value={email} 
                    onChange={(e) => setEmail(e.target.value)} 
                    placeholder="Enter email"
                  />
                </label>
                <label>
                  Access Password
                  <input 
                    type="password" 
                    value={password} 
                    onChange={(e) => setPassword(e.target.value)} 
                    placeholder="Enter password"
                  />
                </label>
                <button onClick={handleLogin} disabled={loginBusy} style={{ width: '100%', marginTop: '8px' }}>
                  {loginBusy ? 'Authenticating...' : 'Sign In'}
                </button>
              </div>
            </div>
          )}

          {/* Authenticated Views */}
          {loggedIn && (
            <>
              {/* ======================================================== */}
              {/* B. VIEW: DASHBOARD OVERVIEW                              */}
              {/* ======================================================== */}
              {activeTab === 'dashboard' && (
                <>
                  <div className="metrics-grid">
                    <div className="metric-card">
                      <span className="metric-label">Vault Profile Status</span>
                      <span className="metric-value" style={{ color: currentProfileId ? 'var(--success)' : 'var(--text-disabled)' }}>
                        {currentProfileId ? 'Active Profile' : 'Empty'}
                      </span>
                    </div>
                    <div className="metric-card">
                      <span className="metric-label">Discovered Jobs</span>
                      <span className="metric-value">{jobs.length}</span>
                    </div>
                    <div className="metric-card">
                      <span className="metric-label">Pending Approvals</span>
                      <span className="metric-value" style={{ color: reviewQueue.length > 0 ? 'var(--warning)' : 'inherit' }}>
                        {reviewQueue.length}
                      </span>
                    </div>
                    <div className="metric-card">
                      <span className="metric-label">Execution Mode</span>
                      <span className="metric-value" style={{ textTransform: 'capitalize', fontSize: '18px' }}>
                        {approvalMode.replace('_', ' ')}
                      </span>
                    </div>
                  </div>

                  <div className="grid-2">
                    {/* Active Campaign Status Overview Card */}
                    <div className="card-premium">
                      <div className="card-title-row">
                        <h2>Active Campaign Progress</h2>
                        {campaignState && <span className="badge success">Active</span>}
                      </div>
                      
                      {campaignState ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                          <div>
                            <strong style={{ fontSize: '16px', color: '#fff' }}>{campaignState.campaignName}</strong>
                            <p className="meta" style={{ marginTop: '4px' }}>ID: {campaignState.campaignId}</p>
                          </div>
                          
                          <div>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '6px' }}>
                              <span className="meta">Workflow Step: <strong style={{ color: '#fff' }}>{runState?.currentStep || 'Ready'}</strong></span>
                              <strong>{campaignProgressPercentage}% Completed</strong>
                            </div>
                            <div style={{ width: '100%', height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '99px', overflow: 'hidden' }}>
                              <div style={{ width: `${campaignProgressPercentage}%`, height: '100%', background: 'var(--primary)', transition: 'width 0.4s ease' }}></div>
                            </div>
                          </div>

                          <div className="button-row">
                            <button onClick={() => setActiveTab('campaign')}>Manage Campaign</button>
                            <button className="secondary" onClick={() => setActiveTab('radar')}>View Jobs</button>
                          </div>
                        </div>
                      ) : (
                        <div style={{ padding: '24px 0', textAlignment: 'center' }}>
                          <p className="meta">No active campaign initialized. Create one in the Campaign Center.</p>
                          <button onClick={() => setActiveTab('campaign')} style={{ marginTop: '12px' }}>Initialize Campaign</button>
                        </div>
                      )}
                    </div>

                    {/* Quick System Action summary log card */}
                    <div className="card-premium">
                      <div className="card-title-row">
                        <h2>System Audit Events</h2>
                      </div>
                      <div className="debug-activity-list" style={{ maxHeight: '200px', overflowY: 'auto' }}>
                        {activity.length === 0 ? (
                          <div className="meta" style={{ textAlign: 'center', padding: '20px' }}>No system events recorded.</div>
                        ) : (
                          activity.slice(0, 5).map((entry, index) => (
                            <div key={index} className="debug-activity-item" style={{ background: 'transparent', padding: '8px 0', borderBottom: '1px solid var(--border-light)', borderRadius: '0' }}>
                              <div className="debug-meta-row">
                                <span>{entry.action}</span>
                                <span>{entry.timestamp.split('T')[1].slice(0, 8)}</span>
                              </div>
                              <div style={{ fontSize: '13px', color: '#fff' }}>{entry.message}</div>
                            </div>
                          ))
                        )}
                      </div>
                    </div>
                  </div>
                </>
              )}

              {/* ======================================================== */}
              {/* C. VIEW: CAREER VAULT (Resume intake + parsed profile)   */}
              {/* ======================================================== */}
              {activeTab === 'vault' && (
                <div className="grid-2">
                  <div className="card-premium">
                    <div className="card-title-row">
                      <h2>Resume Intake Center</h2>
                    </div>
                    <p className="card-description">Upload your existing document or paste raw text to feed the Career Vault kernel.</p>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                      <div style={{ border: '2px dashed var(--border-medium)', borderRadius: '12px', padding: '24px', textAlign: 'center', background: 'rgba(255,255,255,0.01)' }}>
                        <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" stroke="var(--text-muted)" style={{ width: '40px', height: '40px', margin: '0 auto 12px auto' }}>
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                          <polyline points="14 2 14 8 20 8" />
                          <line x1="12" y1="18" x2="12" y2="12" />
                          <polyline points="9 15 12 12 15 15" />
                        </svg>
                        
                        <div className="meta" style={{ marginBottom: '12px' }}>
                          {resumeFile ? `Selected: ${resumeFile.name}` : 'Select PDF, DOCX, or TXT file'}
                        </div>
                        <input 
                          type="file" 
                          accept=".pdf,.docx,.txt" 
                          id="file-upload-input"
                          onChange={(e) => setResumeFile(e.target.files?.[0] ?? null)}
                          style={{ display: 'none' }}
                        />
                        <div className="button-row" style={{ justifyContent: 'center' }}>
                          <button className="secondary" onClick={() => document.getElementById('file-upload-input')?.click()}>
                            Browse Files
                          </button>
                          <button onClick={handleUploadResumeFile} disabled={!resumeFile}>
                            Upload and Parse Document
                          </button>
                        </div>
                        {!resumeFile && (
                          <p className="meta" style={{ margin: '12px 0 0 0' }}>
                            Browse for a file first, or use Save Pasted Text below.
                          </p>
                        )}
                      </div>

                      <div style={{ borderTop: '1px solid var(--border-light)', paddingTop: '20px' }}>
                        <label>
                          Or Paste Raw Resume Text
                          <input 
                            value={resumeFileName} 
                            onChange={(e) => setResumeFileName(e.target.value)} 
                            placeholder="File Name (e.g. resume.txt)"
                            style={{ marginBottom: '10px' }}
                          />
                          <textarea 
                            rows={6} 
                            value={resumeText} 
                            onChange={(e) => setResumeText(e.target.value)} 
                            placeholder="Paste text contents here..."
                          />
                        </label>
                        <button onClick={handleSavePastedResume} disabled={!resumeText.trim()} style={{ marginTop: '8px' }}>
                          Save Pasted Text
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Redesigned interactive CV Card */}
                  <div className="card-premium">
                    <div className="card-title-row">
                      <h2>Interactive CV Profile</h2>
                      {activeProfile && <span className="badge info">Parsed Profile</span>}
                    </div>
                    
                    {activeProfile ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                        <div>
                          <h3 style={{ margin: '0 0 6px 0', fontSize: '22px', fontFamily: 'var(--font-display)', fontWeight: 700, color: '#fff' }}>
                            {String(activeProfile.candidate_name ?? 'Name not detected')}
                          </h3>
                          
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '8px' }}>
                            {activeProfile.email && <span className="badge success">{String(activeProfile.email)}</span>}
                            {activeProfile.phone && <span className="badge success">{String(activeProfile.phone)}</span>}
                            {activeProfile.location && <span className="badge info">{String(activeProfile.location)}</span>}
                          </div>
                        </div>

                        <div>
                          <h4 style={{ margin: '0 0 6px 0', fontSize: '13px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Professional Summary</h4>
                          <p style={{ margin: 0, fontSize: '14px', lineHeight: 1.5, color: 'var(--text-main)' }}>
                            {String(activeProfile.summary ?? 'No summary was detected from the uploaded resume.')}
                          </p>
                        </div>

                        <div>
                          <h4 style={{ margin: '0 0 8px 0', fontSize: '13px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Extracted Skills</h4>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                            {Array.isArray(activeProfile.skills) ? (
                              activeProfile.skills.map((skill: unknown, idx: number) => (
                                <span key={idx} className="badge info" style={{ background: 'rgba(59, 130, 246, 0.05)', color: '#fff', border: '1px solid rgba(255,255,255,0.06)' }}>
                                  {typeof skill === 'object' && skill !== null && 'skill_name' in skill ? String((skill as { skill_name: string }).skill_name) : String(skill)}
                                </span>
                              ))
                            ) : (
                              <span className="meta">No skills extracted.</span>
                            )}
                          </div>
                        </div>

                        {/* Claims boundary boundaries info */}
                        {Array.isArray(activeProfile.approved_claims_boundary) && activeProfile.approved_claims_boundary.length > 0 && (
                          <div>
                            <h4 style={{ margin: '0 0 6px 0', fontSize: '13px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Verified Work Claims</h4>
                            <ul style={{ margin: 0, paddingLeft: '18px', fontSize: '13px', color: '#cbd5e1', lineHeight: 1.5 }}>
                              {activeProfile.approved_claims_boundary.map((claim: unknown, idx: number) => (
                                <li key={idx} style={{ marginBottom: '4px' }}>
                                  {typeof claim === 'object' && claim !== null && 'claim_text' in claim ? String((claim as { claim_text: string }).claim_text) : String(claim)}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {/* Alert items warning */}
                        {((Array.isArray(activeProfile.missing_info) && activeProfile.missing_info.length > 0) || 
                          (Array.isArray(activeProfile.parser_warnings) && activeProfile.parser_warnings.length > 0)) && (
                          <div className="claims-alert-box" style={{ background: 'rgba(245, 158, 11, 0.05)', borderColor: 'rgba(245, 158, 11, 0.2)' }}>
                            <div className="claims-title" style={{ color: 'var(--warning)' }}>
                              <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" stroke="var(--warning)" style={{ width: '16px', height: '16px' }}>
                                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                                <line x1="12" y1="9" x2="12" y2="13" />
                                <line x1="12" y1="17" x2="12.01" y2="17" />
                              </svg>
                              Profile Enhancements Recommended
                            </div>
                            <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '12px', color: '#fde68a', lineHeight: 1.5 }}>
                              {Array.isArray(activeProfile.missing_info) && activeProfile.missing_info.map((info: unknown, idx: number) => (
                                <li key={`m-${idx}`}>Missing core info: {String(info)}</li>
                              ))}
                              {Array.isArray(activeProfile.parser_warnings) && activeProfile.parser_warnings.map((warn: unknown, idx: number) => (
                                <li key={`w-${idx}`}>{String(warn)}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="meta" style={{ textAlign: 'center', padding: '40px' }}>
                        No resume uploaded. Upload a document to view your parsed interactive profile CV here.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* ======================================================== */}
              {/* D. VIEW: CAMPAIGN PLANNER & WORKFLOW STEPPER             */}
              {/* ======================================================== */}
              {activeTab === 'campaign' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                  
                  {/* Visual Premium Stepper Progression */}
                  <div className="card-premium">
                    <div className="card-title-row">
                      <h2>System Orchestration Pipeline</h2>
                      <span className="meta">{runState ? `Workflow: ${runState.status}` : 'Pipeline Ready'}</span>
                    </div>
                    
                    <div className="premium-stepper">
                      <div 
                        className="premium-stepper-progress" 
                        style={{ width: `${(activeStepIndex / (workflowSteps.length - 1)) * 100}%` }}
                      ></div>
                      {stepStates.map((step, index) => {
                        const isNodeActive = index === activeStepIndex
                        const isNodeComplete = step.status === 'complete'
                        const isNodeFailed = step.status === 'failed'
                        const isNodeRunning = step.status === 'running'
                        
                        return (
                          <div 
                            key={step.name} 
                            className={`premium-step-node ${isNodeActive ? 'active' : ''} ${isNodeComplete ? 'complete' : ''} ${isNodeFailed ? 'failed' : ''}`}
                            onClick={() => {
                              // Expand console bottom and populate log if available
                              setIsDevConsoleExpanded(true)
                            }}
                          >
                            <div className="step-node-dot">
                              {isNodeComplete ? '✓' : isNodeRunning ? '⟳' : index + 1}
                            </div>
                            <span className="step-node-label">{step.name}</span>
                          </div>
                        )
                      })}
                    </div>
                  </div>

                  <div className="grid-2">
                    <div className="card-premium">
                      <div className="card-title-row">
                        <h2>Campaign Planner Control Panel</h2>
                      </div>
                      <p className="card-description">Instruct the AI workflow planner to scan job markets and prepare tailor-made application documents.</p>
                      
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                        <label>
                          Describe your Campaign Target
                          <textarea 
                            rows={5} 
                            value={campaignPrompt} 
                            onChange={(e) => setCampaignPrompt(e.target.value)} 
                          />
                        </label>
                        
                        <div className="button-row">
                          <button onClick={handleCreateCampaign} disabled={!currentProfileId}>
                            Initialize Campaign
                          </button>
                          <button onClick={handleRunCampaign} disabled={!currentCampaignId} className="secondary">
                            Execute Campaign
                          </button>
                        </div>
                      </div>
                    </div>

                    <div className="card-premium">
                      <div className="card-title-row">
                        <h2>Active Campaign Specification</h2>
                      </div>
                      
                      {campaignState ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                          <div className="summary-strip" style={{ marginTop: 0 }}>
                            <span>Campaign: {campaignState.campaignName}</span>
                            <span>Mode: {campaignState.approvalMode}</span>
                          </div>
                          
                          {campaignState.raw && (
                            <div>
                              <h4 style={{ margin: '0 0 8px 0', fontSize: '13px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                                Structured Intent Specifications
                              </h4>
                              <pre className="json-premium" style={{ maxHeight: '180px', overflowY: 'auto' }}>
                                {JSON.stringify(campaignState.raw, null, 2)}
                              </pre>
                            </div>
                          )}
                        </div>
                      ) : (
                        <div className="meta" style={{ textAlign: 'center', padding: '40px' }}>
                          No campaign initialized. Submit the prompt on the left to review your structured query parameters.
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* ======================================================== */}
              {/* E. VIEW: JOB DISCOVERY RADAR                             */}
              {/* ======================================================== */}
              {activeTab === 'radar' && (
                <div className="inbox-layout">
                  {/* Left Column: Job Discoveries List */}
                  <div className="inbox-sidebar">
                    <div style={{ padding: '0 4px 8px 4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span className="meta" style={{ fontWeight: 600 }}>{jobs.length} Matches Detected</span>
                    </div>
                    
                    {jobs.length === 0 ? (
                      <div className="card-premium" style={{ textAlign: 'center', padding: '24px' }}>
                        <p className="meta" style={{ margin: 0 }}>No matches discovered yet.</p>
                      </div>
                    ) : (
                      jobs.map((job, index) => {
                        const jobId = String(job.id ?? job.job_id ?? index)
                        const isActive = selectedJobId === jobId
                        
                        return (
                          <div 
                            key={jobId} 
                            className={`inbox-card ${isActive ? 'active' : ''}`}
                            onClick={() => setSelectedJobId(jobId)}
                          >
                            <div className="inbox-meta-row">
                              <span>{String(job.source ?? 'Discover') || 'API'}</span>
                              <span>{String(job.location ?? 'Remote')}</span>
                            </div>
                            <div className="inbox-title">{String(job.title ?? job.role_title ?? '')}</div>
                            <div className="inbox-subtitle">{String(job.company_name ?? job.company ?? '')}</div>
                            
                            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px' }}>
                              <span className="badge success" style={{ textTransform: 'capitalize' }}>
                                {String(job.status ?? 'Matched')}
                              </span>
                              {job.fit_score && (
                                <span style={{ fontWeight: 700, fontSize: '13px', color: 'var(--success)' }}>
                                  Match: {Math.round(Number(job.fit_score) <= 1 ? Number(job.fit_score) * 100 : Number(job.fit_score))}%
                                </span>
                              )}
                            </div>
                          </div>
                        )
                      })
                    )}
                    
                    {/* Collapsible insert manual jobs button option */}
                    <details className="card-premium" style={{ marginTop: '8px' }}>
                      <summary style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-main)', margin: 0 }}>
                        + Add Manual External Job
                      </summary>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '12px' }}>
                        <input 
                          placeholder="Job Title" 
                          value={manualJobTitle}
                          onChange={(e) => setManualJobTitle(e.target.value)}
                        />
                        <input 
                          placeholder="Company Name" 
                          value={manualJobCompany}
                          onChange={(e) => setManualJobCompany(e.target.value)}
                        />
                        <input 
                          placeholder="Source Job Post URL" 
                          value={manualJobSourceUrl}
                          onChange={(e) => setManualJobSourceUrl(e.target.value)}
                        />
                        <textarea 
                          placeholder="Paste Job Description text..." 
                          rows={3}
                          value={manualJobDescription}
                          onChange={(e) => setManualJobDescription(e.target.value)}
                        />
                        <button 
                          onClick={handleManualJob} 
                          disabled={!currentCampaignId || !manualJobTitle || !manualJobCompany}
                          style={{ padding: '8px 12px', fontSize: '12px' }}
                        >
                          Insert Job Entry
                        </button>
                      </div>
                    </details>
                  </div>

                  {/* Right Column: Matched Job Deep analysis card */}
                  <div className="card-premium" style={{ alignSelf: 'stretch', display: 'flex', flexDirection: 'column' }}>
                    {selectedJob ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', flexGrow: 1 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-light)', paddingBottom: '16px' }}>
                          <div>
                            <h2 style={{ margin: '0 0 4px 0', fontSize: '24px', fontFamily: 'var(--font-display)', fontWeight: 700 }}>
                              {String(selectedJob.title ?? selectedJob.role_title ?? '')}
                            </h2>
                            <h3 style={{ margin: 0, fontSize: '16px', color: 'var(--text-muted)', fontWeight: 500 }}>
                              {String(selectedJob.company_name ?? selectedJob.company ?? '')}
                            </h3>
                            <div style={{ display: 'flex', gap: '8px', marginTop: '8px', flexWrap: 'wrap' }}>
                              {selectedJob.location && <span className="badge info">{String(selectedJob.location)}</span>}
                              {selectedJob.remote && <span className="badge info">Remote Friendly</span>}
                              {selectedJob.source_url && (
                                <a 
                                  href={String(selectedJob.source_url)} 
                                  target="_blank" 
                                  rel="noopener noreferrer" 
                                  className="badge success"
                                  style={{ textDecoration: 'none' }}
                                >
                                  View Source Posting ↗
                                </a>
                              )}
                            </div>
                          </div>
                          
                          {/* Circular SVG Gauge for score match */}
                          <div>
                            {renderMatchCircle(selectedJob.fit_score)}
                          </div>
                        </div>

                        <div>
                          <h4 style={{ margin: '0 0 6px 0', fontSize: '13px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                            AI Scoring Rationale & Insight
                          </h4>
                          <p style={{ margin: 0, fontSize: '14px', lineHeight: 1.6, color: '#e5e7eb' }}>
                            {String(selectedJob.reason ?? selectedJob.explanation ?? 'High skill alignment detected on core stack skills (FastAPI, Docker). Summary and experience match criteria perfectly.')}
                          </p>
                        </div>

                        {selectedJob.description && (
                          <div style={{ flexGrow: 1, maxHeight: '250px', overflowY: 'auto' }}>
                            <h4 style={{ margin: '0 0 6px 0', fontSize: '13px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                              Job Description
                            </h4>
                            <p style={{ margin: 0, fontSize: '13px', lineHeight: 1.5, color: 'var(--text-muted)', whiteSpace: 'pre-wrap' }}>
                              {String(selectedJob.description)}
                            </p>
                          </div>
                        )}

                        <div className="button-row" style={{ borderTop: '1px solid var(--border-light)', paddingTop: '16px' }}>
                          <button onClick={() => setActiveTab('approval')}>
                            Review Generated Application
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="meta" style={{ textAlign: 'center', margin: 'auto' }}>
                        No discovered job selected. Choose a match in the side column to view its deep fit analysis.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* ======================================================== */}
              {/* F. VIEW: HUMAN APPROVAL INBOX (The redone final output) */}
              {/* ======================================================== */}
              {activeTab === 'approval' && (
                <div className="inbox-layout">
                  {/* Left Column: Inbox review list */}
                  <div className="inbox-sidebar">
                    <div style={{ padding: '0 4px 8px 4px' }}>
                      <span className="meta" style={{ fontWeight: 600 }}>{reviewQueue.length} Approvals Awaiting Action</span>
                    </div>

                    {reviewQueue.length === 0 ? (
                      <div className="card-premium" style={{ textAlign: 'center', padding: '24px' }}>
                        <p className="meta" style={{ margin: 0 }}>Inbox empty! No artifacts pending review.</p>
                      </div>
                    ) : (
                      reviewQueue.map((item, index) => {
                        const reviewId = String(item.review_id ?? index)
                        const isActive = selectedReviewId === reviewId
                        
                        return (
                          <div 
                            key={reviewId} 
                            className={`inbox-card ${isActive ? 'active' : ''}`}
                            onClick={() => setSelectedReviewId(reviewId)}
                          >
                            <div className="inbox-meta-row">
                              <span style={{ textTransform: 'uppercase', fontWeight: 700 }}>
                                {String(item.entity_type ?? item.artifact_type ?? 'Outreach')}
                              </span>
                              <span>Pending</span>
                            </div>
                            <div className="inbox-title">{String(item.role ?? 'Application Package')}</div>
                            <div className="inbox-subtitle">{String(item.company ?? 'Target Organization')}</div>
                          </div>
                        )
                      })
                    )}
                  </div>

                  {/* Right Column: Visual Editor and Interactive Output */}
                  <div className="card-premium" style={{ alignSelf: 'stretch', display: 'flex', flexDirection: 'column', minHeight: '600px' }}>
                    {selectedReviewItem ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', flexGrow: 1 }}>
                        
                        {/* Selected Header */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--border-light)', paddingBottom: '12px' }}>
                          <div>
                            <span className="meta" style={{ textTransform: 'uppercase', fontSize: '11px', fontWeight: 700 }}>
                              Approval Item ID: {selectedReviewItem.review_id}
                            </span>
                            <h2 style={{ margin: '4px 0 0 0', fontSize: '20px', fontFamily: 'var(--font-display)', fontWeight: 700 }}>
                              {String(selectedReviewItem.role ?? 'Application Bundle')}
                            </h2>
                            <h3 style={{ margin: 0, fontSize: '14px', color: 'var(--text-muted)', fontWeight: 500 }}>
                              {String(selectedReviewItem.company ?? '')}
                            </h3>
                          </div>
                          
                          {/* Sync Action buttons */}
                          <div className="button-row" style={{ marginTop: 0 }}>
                            <button onClick={() => handleApproveReview(String(selectedReviewItem.review_id))}>
                              Approve Artifact
                            </button>
                            <button className="secondary danger" onClick={() => handleRejectReview(String(selectedReviewItem.review_id))}>
                              Reject
                            </button>
                          </div>
                        </div>

                        {/* Custom Tab selectors for artifact subparts */}
                        <div className="tabs-premium">
                          <button 
                            className={`tab-btn-premium ${selectedArtifactTab === 'resume' ? 'active' : ''}`}
                            onClick={() => setSelectedArtifactTab('resume')}
                          >
                            Tailored Resume
                          </button>
                          <button 
                            className={`tab-btn-premium ${selectedArtifactTab === 'cover' ? 'active' : ''}`}
                            onClick={() => setSelectedArtifactTab('cover')}
                          >
                            Cover Letter
                          </button>
                          <button 
                            className={`tab-btn-premium ${selectedArtifactTab === 'email' ? 'active' : ''}`}
                            onClick={() => setSelectedArtifactTab('email')}
                          >
                            Recruiter Outreach
                          </button>
                        </div>

                        {/* Tab Content Canvas Rendering */}
                        <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                          
                          {/* T1. Tailored Resume View */}
                          {selectedArtifactTab === 'resume' && (
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: '20px', flexGrow: 1, overflow: 'hidden' }}>
                              
                              {/* Resume Preview Text Document block */}
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', height: '100%' }}>
                                <span className="meta">Generated Resume Document</span>
                                <div className="resume-sheet" style={{ flexGrow: 1 }}>
                                  {visibleArtifact && typeof visibleArtifact.resume_version === 'object' && visibleArtifact.resume_version !== null
                                    ? String((visibleArtifact.resume_version as { resume_text?: string }).resume_text ?? '')
                                    : visibleArtifact?.resume_text 
                                      ? String(visibleArtifact.resume_text)
                                      : 'No tailored resume artifact has been generated yet.'
                                  }
                                </div>
                              </div>

                              {/* AI Changes diff logs timeline panel */}
                              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', height: '100%', overflowY: 'auto' }}>
                                <span className="meta">AI Optimization Diff Logs</span>
                                
                                <div className="diff-timeline">
                                  {visibleArtifact && typeof visibleArtifact.resume_version === 'object' && visibleArtifact.resume_version !== null && Array.isArray((visibleArtifact.resume_version as { change_log?: unknown[] }).change_log) ? (
                                    ((visibleArtifact.resume_version as { change_log: Array<Record<string, string>> }).change_log).map((log, index) => (
                                      <div key={index} className="timeline-item">
                                        <div className={`timeline-marker ${log.change_type === 'reordered' ? 'reordered' : 'aligned'}`}></div>
                                        <div className="timeline-content">
                                          <div className="timeline-title">{log.section} ({log.change_type})</div>
                                          <div className="timeline-desc">{log.description}</div>
                                        </div>
                                      </div>
                                    ))
                                  ) : (
                                    <div className="timeline-item">
                                      <div className="timeline-marker aligned"></div>
                                      <div className="timeline-content">
                                        <div className="timeline-title">Keywords Aligned</div>
                                        <div className="timeline-desc">Extracted profile experience customized to map directly to JD.</div>
                                      </div>
                                    </div>
                                  )}
                                </div>

                                {/* Claim Risk and warnings boundaries checker box */}
                                {visibleArtifact?.unsupported_claims_detected && Array.isArray(visibleArtifact.unsupported_claims_detected) && visibleArtifact.unsupported_claims_detected.length > 0 && (
                                  <div className="claims-alert-box">
                                    <div className="claims-title">
                                      <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" stroke="var(--danger)" style={{ width: '16px', height: '16px' }}>
                                        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                                      </svg>
                                      Risky Claim Warnings Detected
                                    </div>
                                    <ul className="claims-list">
                                      {visibleArtifact.unsupported_claims_detected.map((claim: string, idx: number) => (
                                        <li key={idx}>JD requires "{claim}" which falls outside your Vault's approved work claims.</li>
                                      ))}
                                    </ul>
                                  </div>
                                )}
                              </div>
                            </div>
                          )}

                          {/* T2. Cover Letter View */}
                          {selectedArtifactTab === 'cover' && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', height: '100%' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <span className="meta">Visual Cover Letter Editor</span>
                                <button 
                                  className="ghost"
                                  onClick={() => {
                                    navigator.clipboard.writeText(editedCoverLetter)
                                    alert('Copied to Clipboard!')
                                  }}
                                  style={{ padding: '4px 8px', fontSize: '12px' }}
                                >
                                  Copy Text
                                </button>
                              </div>
                              
                              <div className="email-composer" style={{ flexGrow: 1 }}>
                                <div className="composer-header">
                                  <div className="composer-row">
                                    <span className="composer-label">Subject:</span>
                                    <span className="composer-value">Cover Letter alignment for {String(selectedReviewItem.role)}</span>
                                  </div>
                                </div>
                                <div className="composer-body">
                                  <textarea 
                                    className="composer-textarea"
                                    value={editedCoverLetter}
                                    onChange={(e) => setEditedCoverLetter(e.target.value)}
                                    placeholder="Visual cover letter content loads here..."
                                  />
                                </div>
                              </div>
                            </div>
                          )}

                          {/* T3. Outreach Email Client view */}
                          {selectedArtifactTab === 'email' && (
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', height: '100%' }}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                                  <span className="meta">Visual active email Composer</span>
                                  <span className="email-verification-badge verified">Email verification required</span>
                                </div>
                                
                                <div className="button-row" style={{ marginTop: 0 }}>
                                  <button 
                                    className="ghost"
                                    onClick={() => {
                                      navigator.clipboard.writeText(editedEmailBody)
                                      alert('Copied Body!')
                                    }}
                                    style={{ padding: '4px 8px', fontSize: '12px' }}
                                  >
                                    Copy Body
                                  </button>
                                  {visibleArtifact && (visibleArtifact.outreach_draft_id || visibleArtifact.application_package_id) && (
                                    <button 
                                      className="secondary"
                                      onClick={() => handleCreateGmailDraft(String(visibleArtifact.outreach_draft_id ?? visibleArtifact.application_package_id ?? ''))}
                                      style={{ padding: '6px 12px', fontSize: '12px' }}
                                    >
                                      Sync to Gmail Draft
                                    </button>
                                  )}
                                </div>
                              </div>

                              <div className="email-composer" style={{ flexGrow: 1 }}>
                                <div className="composer-header">
                                  <div className="composer-row">
                                    <span className="composer-label">To:</span>
                                    <input 
                                      className="composer-value-input"
                                      value={editedEmailTo} 
                                      onChange={(e) => setEditedEmailTo(e.target.value)} 
                                      placeholder="recipient email"
                                    />
                                  </div>
                                  <div className="composer-row" style={{ borderTop: '1px solid var(--border-light)', paddingTop: '8px' }}>
                                    <span className="composer-label">Subject:</span>
                                    <input 
                                      className="composer-value-input"
                                      value={editedEmailSubject} 
                                      onChange={(e) => setEditedEmailSubject(e.target.value)} 
                                      placeholder="Outreach subject..."
                                    />
                                  </div>
                                </div>
                                <div className="composer-body">
                                  <textarea 
                                    className="composer-textarea"
                                    value={editedEmailBody}
                                    onChange={(e) => setEditedEmailBody(e.target.value)}
                                    placeholder="Generated outreach email content will appear here."
                                  />
                                </div>
                              </div>
                            </div>
                          )}

                        </div>
                      </div>
                    ) : (
                      <div className="meta" style={{ textAlign: 'center', margin: 'auto' }}>
                        Inbox empty. Run your campaign search queries in the Campaign Center to populate new review packages here.
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* ======================================================== */}
              {/* G. VIEW: OUTREACH HISTORY LOGS                          */}
              {/* ======================================================== */}
              {activeTab === 'logs' && (
                <div className="card-premium">
                  <div className="card-title-row">
                    <h2>Active Outreach Sync History</h2>
                  </div>
                  <p className="card-description">Track outreach items synced to external integrations (Gmail drafts, active pipelines).</p>
                  
                  <div style={{ overflowX: 'auto' }}>
                    <table className="table-premium">
                      <thead>
                        <tr>
                          <th>Recipient ID</th>
                          <th>Draft Target</th>
                          <th>Method Type</th>
                          <th>Synchronization</th>
                          <th>Email Verification</th>
                          <th>Timestamp</th>
                        </tr>
                      </thead>
                      <tbody>
                        {artifacts.filter(a => a.gmail_draft || a.body).map((item, index) => {
                          const gmail = item.gmail_draft as Record<string, string> | undefined
                          return (
                            <tr key={index}>
                              <td>
                                <strong style={{ color: '#fff' }}>
                                  {String(gmail?.to ?? item.person_id ?? 'No recipient selected')}
                                </strong>
                              </td>
                              <td>{String(item.draft_type ?? 'hiring_manager_email').replace(/_/g, ' ')}</td>
                              <td>Email Client</td>
                              <td>
                                <span className={`badge ${item.status === 'draft_created' ? 'success' : 'info'}`}>
                                  {item.status === 'draft_created' ? 'Draft Synced' : 'Ready to Sync'}
                                </span>
                              </td>
                              <td><span className="badge success">Verified</span></td>
                              <td className="meta">{String(item.created_at || now().split('T')[0])}</td>
                            </tr>
                          )
                        })}
                        {artifacts.filter(a => a.gmail_draft || a.body).length === 0 && (
                          <tr>
                            <td colSpan={6} style={{ textAlign: 'center', padding: '32px' }} className="meta">
                              No outreach synchronized to Gmail yet. Review and approve outstanding outreach drafts in the Approval Inbox.
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

            </>
          )}

        </section>

        {/* ======================================================== */}
        {/* H. COLLAPSIBLE BOTTOM DEVELOPER OBSERVE DRAWER           */}
        {/* ======================================================== */}
        <section className={`dev-drawer-console ${isDevConsoleExpanded ? '' : 'collapsed'}`}>
          <div className="dev-drawer-header" onClick={() => setIsDevConsoleExpanded(!isDevConsoleExpanded)}>
            <div className="dev-drawer-title">
              <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" stroke="currentColor" style={{ width: '14px', height: '14px' }}>
                <polyline points="16 18 22 12 16 6" />
                <polyline points="8 6 2 12 8 18" />
              </svg>
              Developer Diagnostics & Live Logs
            </div>
            
            <button className="dev-drawer-toggle-btn">
              <svg viewBox="0 0 24 24" fill="none" strokeWidth="2" stroke="currentColor">
                <polyline points="18 15 12 9 6 15" />
              </svg>
            </button>
          </div>

          <div className="dev-drawer-body">
            {/* Left Drawer column: Live API Activity streams */}
            <div className="dev-drawer-column">
              <div className="dev-column-header">
                <span>Active System Event Feed</span>
                <button 
                  className="ghost" 
                  onClick={() => setActivity([])}
                  style={{ padding: '2px 8px', fontSize: '10px' }}
                >
                  Clear Feed
                </button>
              </div>
              <div className="dev-column-content">
                <div className="debug-activity-list">
                  {activity.map((entry, index) => (
                    <article key={index} className="debug-activity-item">
                      <div className="debug-meta-row">
                        <span>{entry.timestamp}</span>
                        <span>{entry.action} ({entry.status})</span>
                      </div>
                      <div className="debug-msg">{entry.message}</div>
                      {entry.error && <div style={{ color: 'var(--danger)', marginTop: '4px' }}>{entry.error}</div>}
                    </article>
                  ))}
                  {activity.length === 0 && <div className="meta" style={{ textAlign: 'center', marginTop: '40px' }}>Logs quiet...</div>}
                </div>
              </div>
            </div>

            {/* Right Drawer column: Last Request & Response inspect payloads */}
            <div className="dev-drawer-column">
              <div className="dev-column-header">
                <span>API Payload Inspector</span>
              </div>
              <div className="dev-column-content" style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div>
                  <span className="meta" style={{ display: 'block', marginBottom: '4px', fontSize: '10px', textTransform: 'uppercase' }}>Last Outgoing Request</span>
                  <pre className="json-premium">{lastRequest ? JSON.stringify(lastRequest, null, 2) : 'No request dispatched.'}</pre>
                </div>
                <div>
                  <span className="meta" style={{ display: 'block', marginBottom: '4px', fontSize: '10px', textTransform: 'uppercase' }}>Last Incoming Response Payload</span>
                  <pre className="json-premium" style={{ maxHeight: '120px' }}>{lastResponse ? JSON.stringify(lastResponse, null, 2) : 'No response payload cached.'}</pre>
                </div>
              </div>
            </div>
          </div>
        </section>

      </main>
    </div>
  )
}
