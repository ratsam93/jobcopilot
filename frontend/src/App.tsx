import { useEffect, useMemo, useState } from 'react'
import { api } from './api'

type LogLine = { kind: 'info' | 'error'; message: string }

const samplePrompt =
  'Apply to top technology companies across the USA where I am fit. Prepare resume, cover letter, find hiring manager and recruiter, but do not send anything without my approval.'

const workflowSteps = [
  {
    title: '1. Intake',
    body: 'Upload the resume and create a Career Vault profile with approved claims, skills, and do-not-claim guardrails.',
  },
  {
    title: '2. Parse',
    body: 'Convert the campaign prompt into a structured query with countries, locations, fit thresholds, and asset preferences.',
  },
  {
    title: '3. Discover',
    body: 'Normalize jobs, remove duplicates, score fit, and shortlist only the jobs that pass the threshold.',
  },
  {
    title: '4. Prepare',
    body: 'Generate the tailored resume, cover letter, recruiter email, hiring manager email, referral note, and call script.',
  },
  {
    title: '5. Approve',
    body: 'Keep everything pending_review until a human approves drafts and the system can create final sendable artifacts.',
  },
]

const apiMap = [
  { method: 'GET', path: '/api/health', description: 'Backend status for the UI shell.' },
  { method: 'GET', path: '/api/health/database', description: 'Postgres readiness and connection check.' },
  { method: 'POST', path: '/api/career-vault/resume/upload', description: 'Create or update a Career Vault profile from the resume text.' },
  { method: 'POST', path: '/api/campaigns/create', description: 'Parse the campaign prompt into structured campaign JSON.' },
  { method: 'POST', path: '/api/campaigns/{campaign_id}/run', description: 'Run discovery, scoring, packaging, and review staging.' },
  { method: 'GET', path: '/api/campaigns/{campaign_id}/status', description: 'Fetch campaign status and current workflow state.' },
  { method: 'GET', path: '/api/campaigns/{campaign_id}/jobs', description: 'List shortlisted jobs queued by the campaign.' },
]

const applicationFlow = [
  'Resume upload creates the Career Vault profile.',
  'Campaign prompt is parsed into a structured query.',
  'Job discovery normalizes sources and removes duplicates.',
  'Fit scorer filters out wrong-fit jobs.',
  'Document generator produces tailored resume and outreach drafts.',
  'Review queue holds everything until approval.',
]

export default function App() {
  const [health, setHealth] = useState<string>('unknown')
  const [resumeText, setResumeText] = useState<string>(
    'Sam Patel\nAI Consultant\n\nAI automation, FastAPI, SQL, Postgres, Docker, AWS, LLMs\n\n- Built AI automation workflows for consulting clients.\n- Led backend APIs using FastAPI and SQL.\n',
  )
  const [resumeFileName, setResumeFileName] = useState('sample_resume_ai_consultant.txt')
  const [profileId, setProfileId] = useState<string>('')
  const [campaignPrompt, setCampaignPrompt] = useState(samplePrompt)
  const [campaignId, setCampaignId] = useState<string>('')
  const [campaignStatus, setCampaignStatus] = useState<Record<string, unknown> | null>(null)
  const [campaignJobs, setCampaignJobs] = useState<Array<Record<string, unknown>>>([])
  const [logs, setLogs] = useState<LogLine[]>([])

  const refreshHealth = async () => {
    try {
      const value = await api.health()
      setHealth(value.status)
    } catch {
      setHealth('offline')
    }
  }

  useEffect(() => {
    void refreshHealth()
  }, [])

  const stats = useMemo(
    () => ({
      jobs: campaignJobs.length,
      status: String(campaignStatus?.status ?? 'not started'),
      approval: String(campaignStatus?.execution_mode ?? 'approval_required'),
    }),
    [campaignJobs.length, campaignStatus],
  )

  const pushLog = (kind: LogLine['kind'], message: string) => setLogs((items) => [{ kind, message }, ...items].slice(0, 12))

  const refreshCampaign = async (id: string) => {
    const [status, jobs] = await Promise.all([api.campaignStatus(id), api.campaignJobs(id)])
    setCampaignStatus(status)
    setCampaignJobs(jobs)
  }

  const handleResumeUpload = async () => {
    try {
      const result = await api.uploadResume(resumeFileName, resumeText)
      setProfileId(result.candidate_profile_id)
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
      pushLog('info', `Campaign run completed with ${campaignJobs.length} queued jobs`)
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

  return (
    <main className="shell">
      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Job Copilot Platform</p>
          <h1>Run job campaigns from one control surface.</h1>
          <p className="lede">
            The UI now follows the real workflow: intake, parse, discover, prepare, and approve. It also shows the
            API surfaces that back each step so the flow is explicit instead of hidden.
          </p>
          <div className="hero-actions">
            <button onClick={handleCampaignRun} disabled={!campaignId}>
              Execute flow
            </button>
            <button className="secondary" onClick={handleRefreshStatus} disabled={!campaignId}>
              Refresh status
            </button>
            <span className="health">Backend: {health}</span>
          </div>
        </div>
        <div className="hero-card">
          <div className="hero-stat">
            <span>Campaign</span>
            <strong>{stats.status}</strong>
          </div>
          <div className="hero-stat">
            <span>Approval</span>
            <strong>{stats.approval}</strong>
          </div>
          <div className="hero-stat">
            <span>Jobs</span>
            <strong>{stats.jobs}</strong>
          </div>
        </div>
      </section>

      <section className="topbar">
        <div className="strip-item">
          <span>Profile</span>
          <strong>{profileId || 'not created'}</strong>
        </div>
        <div className="strip-item">
          <span>Campaign</span>
          <strong>{campaignId || 'not created'}</strong>
        </div>
        <div className="strip-item">
          <span>Queued jobs</span>
          <strong>{campaignJobs.length}</strong>
        </div>
      </section>

      <section className="grid">
        <article className="panel">
          <h2>Workflow Flow</h2>
          <div className="timeline">
            {workflowSteps.map((step) => (
              <div key={step.title} className="timeline-item">
                <h3>{step.title}</h3>
                <p>{step.body}</p>
              </div>
            ))}
          </div>
        </article>

        <article className="panel">
          <h2>What Gets Created</h2>
          <ul className="checklist">
            <li>Tailored resume from approved claims only.</li>
            <li>Cover letter, recruiter email, hiring manager email.</li>
            <li>Referral note and call script for follow-up outreach.</li>
            <li>Job shortlist with deduped, scored opportunities.</li>
            <li>Pending review state before anything is sent.</li>
          </ul>
        </article>
      </section>

      <section className="grid">
        <article className="panel">
          <h2>How A Job Is Applied</h2>
          <ol className="ordered">
            {applicationFlow.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ol>
          <div className="meta">
            Send gate: no email or submission is allowed until approval is explicitly granted.
          </div>
        </article>

        <article className="panel">
          <h2>API Connections</h2>
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
      </section>

      <section className="grid">
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
          <button onClick={handleResumeUpload}>Upload resume</button>
          <div className="meta">Profile ID: {profileId || 'not created'}</div>
        </article>

        <article className="panel">
          <h2>Campaign Planner</h2>
          <label>
            Campaign prompt
            <textarea value={campaignPrompt} onChange={(e) => setCampaignPrompt(e.target.value)} rows={10} />
          </label>
          <button onClick={handleCampaignCreate}>Create campaign</button>
          <button onClick={handleCampaignRun} disabled={!campaignId}>
            Run campaign
          </button>
          <div className="meta">Campaign ID: {campaignId || 'not created'}</div>
        </article>
      </section>

      <section className="grid">
        <article className="panel">
          <h2>Workflow Status</h2>
          <div className="status-grid">
            <div className="stat">Campaign status: {stats.status}</div>
            <div className="stat">Approval mode: {stats.approval}</div>
            <div className="stat">Jobs discovered: {stats.jobs}</div>
          </div>
          <pre className="json">{campaignStatus ? JSON.stringify(campaignStatus, null, 2) : 'No status yet'}</pre>
        </article>

        <article className="panel">
          <h2>Generated Output</h2>
          <div className="artifact-card">
            <h3>Resume / Cover Letter / Outreach</h3>
            <p>Generated after the campaign is run, then held in review until approved.</p>
          </div>
          <div className="artifact-card">
            <h3>Email Signing</h3>
            <p>
              The system should sign outbound drafts with the authenticated account after the review gate clears. The
              UI highlights this as the final approval step rather than auto-send.
            </p>
          </div>
          <div className="artifact-card">
            <h3>Approval Status</h3>
            <p>Nothing is sent or submitted until the workflow status moves from pending_review to approved.</p>
          </div>
        </article>
      </section>

      <section className="panel wide">
        <h2>Activity Log</h2>
        <ul className="loglist">
          {logs.map((item, index) => (
            <li key={`${item.message}-${index}`} className={item.kind}>
              {item.message}
            </li>
          ))}
        </ul>
      </section>

      <section className="panel wide">
        <h2>Queued Jobs</h2>
        <pre className="json">{JSON.stringify(campaignJobs, null, 2)}</pre>
      </section>
    </main>
  )
}
