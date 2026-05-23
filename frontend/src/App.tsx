import { useEffect, useMemo, useState } from 'react'
import { api, clearToken, getToken, setToken } from './api'

type LogLine = { kind: 'info' | 'error'; message: string }

const samplePrompt =
  'Apply to top technology companies across the USA where I am fit. Prepare resume, cover letter, find hiring manager and recruiter, but do not send anything without my approval.'

const workflowSteps = [
  { id: 'intake', title: 'Intake', detail: 'Upload resume and create the Career Vault profile.' },
  { id: 'parse', title: 'Parse', detail: 'Convert the campaign prompt into structured campaign JSON.' },
  { id: 'discover', title: 'Discover', detail: 'Normalize jobs, remove duplicates, and score fit.' },
  { id: 'prepare', title: 'Prepare', detail: 'Generate resume, cover letter, outreach drafts, and scripts.' },
  { id: 'approve', title: 'Approve', detail: 'Hold everything in pending_review until approval is granted.' },
]

const apiMap = [
  { method: 'GET', path: '/api/health', description: 'Backend status.' },
  { method: 'GET', path: '/api/health/database', description: 'Postgres readiness.' },
  { method: 'POST', path: '/api/auth/login', description: 'JWT login.' },
  { method: 'POST', path: '/api/career-vault/resume/upload', description: 'Create Career Vault profile.' },
  { method: 'POST', path: '/api/campaigns/create', description: 'Create structured campaign.' },
  { method: 'POST', path: '/api/campaigns/{campaign_id}/run', description: 'Queue workflow run.' },
  { method: 'GET', path: '/api/campaigns/{campaign_id}/status', description: 'Campaign state.' },
  { method: 'GET', path: '/api/campaigns/{campaign_id}/jobs', description: 'Shortlisted jobs.' },
  { method: 'POST', path: '/api/outreach-drafts/gmail-draft', description: 'Create Gmail draft only.' },
]

const applicationFlow = [
  'Resume upload creates the Career Vault profile.',
  'Campaign prompt is parsed into a structured query.',
  'Job discovery normalizes sources and removes duplicates.',
  'Fit scoring filters out wrong-fit jobs.',
  'Document generation creates tailored assets.',
  'Review queue holds everything until approval.',
]

const workflowCards = [
  {
    title: '1. Intake',
    body: 'Upload a resume, create the profile, and lock the approved claims boundary.',
  },
  {
    title: '2. Parse & Score',
    body: 'Create the campaign, discover jobs, and shortlist only fit opportunities.',
  },
  {
    title: '3. Prepare Drafts',
    body: 'Generate the tailored resume, cover letter, email drafts, and scripts.',
  },
  {
    title: '4. Review Gate',
    body: 'Nothing sends or applies until the queue moves to approved.',
  },
]

export default function App() {
  const [token, setTokenState] = useState<string>(getToken() ?? '')
  const [email, setEmail] = useState('admin@jobcopilot.local')
  const [password, setPassword] = useState('admin123')
  const [health, setHealth] = useState<'loading' | 'ok' | 'offline'>('loading')
  const [resumeText, setResumeText] = useState(
    'Sam Patel\nAI Consultant\n\nAI automation, FastAPI, SQL, Postgres, Docker, AWS, LLMs\n\n- Built AI automation workflows for consulting clients.\n- Led backend APIs using FastAPI and SQL.\n',
  )
  const [resumeFileName, setResumeFileName] = useState('sample_resume_ai_consultant.txt')
  const [profileId, setProfileId] = useState('')
  const [campaignPrompt, setCampaignPrompt] = useState(samplePrompt)
  const [campaignId, setCampaignId] = useState('')
  const [campaignStatus, setCampaignStatus] = useState<Record<string, unknown> | null>(null)
  const [campaignJobs, setCampaignJobs] = useState<Array<Record<string, unknown>>>([])
  const [outreachDraftId, setOutreachDraftId] = useState('')
  const [activeStep, setActiveStep] = useState(0)
  const [logs, setLogs] = useState<LogLine[]>([])

  const pushLog = (kind: LogLine['kind'], message: string) =>
    setLogs((items) => [{ kind, message }, ...items].slice(0, 12))

  const refreshHealth = async () => {
    try {
      const value = await api.health()
      setHealth(value.status === 'ok' ? 'ok' : 'offline')
    } catch {
      setHealth('offline')
    }
  }

  useEffect(() => {
    void refreshHealth()
  }, [])

  const handleLogin = async () => {
    try {
      const result = await api.login(email, password)
      setToken(result.access_token)
      setTokenState(result.access_token)
      pushLog('info', `Logged in as ${result.user.email}`)
    } catch (error) {
      pushLog('error', `Login failed: ${String(error)}`)
    }
  }

  const handleLogout = () => {
    clearToken()
    setTokenState('')
    pushLog('info', 'Logged out')
  }

  const refreshCampaign = async (id: string) => {
    const [status, jobs] = await Promise.all([api.campaignStatus(id), api.campaignJobs(id)])
    setCampaignStatus(status)
    setCampaignJobs(jobs)
    setActiveStep(jobs.length > 0 ? 4 : 2)
  }

  const handleResumeUpload = async () => {
    try {
      const result = await api.uploadResume(resumeFileName, resumeText)
      setProfileId(result.candidate_profile_id)
      setActiveStep(1)
      pushLog('info', `Career Vault profile ready: ${result.created_profile.full_name ?? 'unknown'}`)
    } catch (error) {
      pushLog('error', `Resume upload failed: ${String(error)}`)
    }
  }

  const handleCampaignCreate = async () => {
    try {
      const result = await api.createCampaign({
        natural_language_prompt: campaignPrompt,
        execution_mode: 'approval_required',
        candidate_profile_id: profileId || undefined,
      })
      setCampaignId(result.campaign_id)
      setActiveStep(2)
      pushLog('info', `Campaign created: ${result.campaign_name}`)
    } catch (error) {
      pushLog('error', `Campaign creation failed: ${String(error)}`)
    }
  }

  const handleCampaignRun = async () => {
    if (!campaignId) return
    try {
      await api.runCampaign(campaignId)
      await refreshCampaign(campaignId)
      pushLog('info', 'Campaign queued and workflow state refreshed')
    } catch (error) {
      pushLog('error', `Campaign run failed: ${String(error)}`)
    }
  }

  const handleRefreshStatus = async () => {
    if (!campaignId) return
    try {
      await refreshCampaign(campaignId)
      pushLog('info', 'Campaign status refreshed')
    } catch (error) {
      pushLog('error', `Status refresh failed: ${String(error)}`)
    }
  }

  const handleCreateGmailDraft = async () => {
    if (!outreachDraftId) return
    try {
      const result = await api.createGmailDraft(outreachDraftId)
      pushLog('info', `Gmail draft created: ${result.gmail_draft_id}`)
    } catch (error) {
      pushLog('error', `Gmail draft failed: ${String(error)}`)
    }
  }

  const stats = useMemo(
    () => ({
      jobs: campaignJobs.length,
      status: String(campaignStatus?.status ?? 'not started'),
      approval: String(campaignStatus?.execution_mode ?? 'approval_required'),
      profile: profileId ? 'created' : 'not created',
      campaign: campaignId ? 'created' : 'not created',
      auth: token ? 'signed in' : 'signed out',
    }),
    [campaignJobs.length, campaignId, campaignStatus, profileId, token],
  )

  return (
    <main className="shell">
      <header className="page-header">
        <div>
          <p className="eyebrow">Job Copilot Platform</p>
          <h1>Run job campaigns from one control surface.</h1>
          <p className="lede">
            The UI is organized around the real workflow: intake, parse, discover, prepare, and approve. Actions are
            grouped by what the user is trying to do, not by backend implementation details.
          </p>
        </div>
        <aside className="header-stats">
          <div className="hero-stat">
            <span>Backend</span>
            <strong className={health}>{health}</strong>
          </div>
          <div className="hero-stat">
            <span>Auth</span>
            <strong>{stats.auth}</strong>
          </div>
          <div className="hero-stat">
            <span>Approval</span>
            <strong>{stats.approval}</strong>
          </div>
        </aside>
      </header>

      <section className="toolbar">
        <button onClick={handleCampaignRun} disabled={!campaignId}>
          Execute flow
        </button>
        <button className="secondary" onClick={handleRefreshStatus} disabled={!campaignId}>
          Refresh status
        </button>
        <button className="secondary" onClick={refreshHealth}>
          Check backend
        </button>
        <span className="pill">Step {activeStep + 1} of {workflowSteps.length}</span>
      </section>

      <section className="top-metrics">
        <div className="metric-card">
          <span>Profile</span>
          <strong>{stats.profile}</strong>
        </div>
        <div className="metric-card">
          <span>Campaign</span>
          <strong>{stats.campaign}</strong>
        </div>
        <div className="metric-card">
          <span>Queued jobs</span>
          <strong>{stats.jobs}</strong>
        </div>
        <div className="metric-card">
          <span>Campaign status</span>
          <strong>{stats.status}</strong>
        </div>
      </section>

      <section className="layout">
        <aside className="sidebar panel">
          <h2>Workflow</h2>
          <div className="step-list">
            {workflowSteps.map((step, index) => {
              const isActive = index === activeStep
              const isDone = index < activeStep
              return (
                <button
                  key={step.id}
                  className={`step-row ${isActive ? 'active' : ''} ${isDone ? 'done' : ''}`}
                  onClick={() => setActiveStep(index)}
                >
                  <span className="step-index">{index + 1}</span>
                  <span className="step-copy">
                    <strong>{step.title}</strong>
                    <small>{step.detail}</small>
                  </span>
                </button>
              )
            })}
          </div>

          <div className="side-summary">
            <h3>Current state</h3>
            <p>Profile: {stats.profile}</p>
            <p>Campaign: {stats.campaign}</p>
            <p>Jobs: {stats.jobs}</p>
          </div>
        </aside>

        <section className="content">
          <article className="panel spotlight">
            <div className="spotlight-head">
              <div>
                <h2>What this flow does</h2>
                <p>
                  The product should feel like an operator console. Each action maps to a real backend step and the
                  user always sees where the workflow is blocked.
                </p>
              </div>
              <div className="status-chip">pending_review</div>
            </div>

            <div className="workflow-grid">
              {workflowCards.map((card, index) => (
                <div key={card.title} className={`workflow-card ${index === activeStep ? 'selected' : ''}`}>
                  <span className="workflow-number">{index + 1}</span>
                  <div>
                    <h3>{card.title}</h3>
                    <p>{card.body}</p>
                  </div>
                </div>
              ))}
            </div>
          </article>

          <div className="split">
            <article className="panel">
              <h2>Login</h2>
              <div className="form-grid">
                <label>
                  Email
                  <input value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="username" />
                </label>
                <label>
                  Password
                  <input
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    type="password"
                    autoComplete="current-password"
                  />
                </label>
              </div>
              <div className="button-row">
                <button onClick={handleLogin}>Log in</button>
                <button className="secondary" onClick={handleLogout} disabled={!token}>
                  Log out
                </button>
              </div>
              <div className="meta">Session token: {token ? 'stored in sessionStorage' : 'not set'}</div>
            </article>

            <article className="panel">
              <h2>How a job is applied</h2>
              <ol className="ordered">
                {applicationFlow.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ol>
              <div className="meta">Nothing sends or submits until the review gate is approved.</div>
            </article>
          </div>

          <div className="split">
            <article className="panel">
              <h2>Career Vault</h2>
              <label>
                Resume filename
                <input value={resumeFileName} onChange={(e) => setResumeFileName(e.target.value)} />
              </label>
              <label>
                Resume text
                <textarea value={resumeText} onChange={(e) => setResumeText(e.target.value)} rows={10} />
              </label>
              <div className="button-row">
                <button onClick={handleResumeUpload}>Upload resume</button>
              </div>
              <div className="meta">Profile ID: {profileId || 'not created'}</div>
            </article>

            <article className="panel">
              <h2>Campaign Planner</h2>
              <label>
                Campaign prompt
                <textarea value={campaignPrompt} onChange={(e) => setCampaignPrompt(e.target.value)} rows={10} />
              </label>
              <div className="button-row">
                <button onClick={handleCampaignCreate}>Create campaign</button>
                <button onClick={handleCampaignRun} disabled={!campaignId}>
                  Run campaign
                </button>
              </div>
              <div className="meta">Campaign ID: {campaignId || 'not created'}</div>
            </article>
          </div>

          <div className="split">
            <article className="panel">
              <h2>Generated output</h2>
              <div className="artifact-card">
                <h3>Resume / cover letter / outreach</h3>
                <p>Generated after the campaign is run, then held in review until approved.</p>
              </div>
              <div className="artifact-card">
                <h3>Email signing</h3>
                <p>
                  Outbound drafts are signed from the authenticated account after review. The UI keeps this explicit.
                </p>
              </div>
              <div className="artifact-card">
                <h3>Gmail draft</h3>
                <p>Create a Gmail draft from an approved outreach message. The system does not auto-send.</p>
                <label>
                  Outreach draft ID
                  <input value={outreachDraftId} onChange={(e) => setOutreachDraftId(e.target.value)} />
                </label>
                <button onClick={handleCreateGmailDraft} disabled={!outreachDraftId}>
                  Create Gmail Draft
                </button>
              </div>
            </article>

            <article className="panel">
              <h2>What gets created</h2>
              <ul className="checklist">
                <li>Tailored resume from approved claims only.</li>
                <li>Cover letter, recruiter email, hiring manager email.</li>
                <li>Referral note and call script for follow-up outreach.</li>
                <li>Job shortlist with deduped, scored opportunities.</li>
                <li>Pending review state before anything is sent.</li>
              </ul>
            </article>
          </div>

          <div className="split">
            <article className="panel">
              <h2>API connections</h2>
              <div className="api-table">
                {apiMap.map((item) => (
                  <div key={item.path} className="api-row">
                    <span className="api-method">{item.method}</span>
                    <code>{item.path}</code>
                    <p>{item.description}</p>
                  </div>
                ))}
              </div>
            </article>

            <article className="panel">
              <h2>Workflow status</h2>
              <div className="status-grid">
                <div className="stat">Campaign status: {stats.status}</div>
                <div className="stat">Approval mode: {stats.approval}</div>
                <div className="stat">Jobs discovered: {stats.jobs}</div>
              </div>
              <pre className="json">{campaignStatus ? JSON.stringify(campaignStatus, null, 2) : 'No status yet'}</pre>
            </article>
          </div>

          <section className="panel">
            <h2>Queued jobs</h2>
            <pre className="json">{JSON.stringify(campaignJobs, null, 2)}</pre>
          </section>

          <section className="panel">
            <h2>Activity log</h2>
            <ul className="loglist">
              {logs.map((item, index) => (
                <li key={`${item.message}-${index}`} className={item.kind}>
                  {item.message}
                </li>
              ))}
            </ul>
          </section>
        </section>
      </section>
    </main>
  )
}
