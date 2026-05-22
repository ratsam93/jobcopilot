import { useEffect, useMemo, useState } from 'react'
import { api } from './api'

type LogLine = { kind: 'info' | 'error'; message: string }

const samplePrompt =
  'Apply to top technology companies across the USA where I am fit. Prepare resume, cover letter, find hiring manager and recruiter, but do not send anything without my approval.'

export default function App() {
  const [health, setHealth] = useState<string>('unknown')
  const [resumeText, setResumeText] = useState<string>('Sam Patel\nAI Consultant\n\nAI automation, FastAPI, SQL, Postgres, Docker, AWS, LLMs\n\n- Built AI automation workflows for consulting clients.\n- Led backend APIs using FastAPI and SQL.\n')
  const [resumeFileName, setResumeFileName] = useState('sample_resume_ai_consultant.txt')
  const [profileId, setProfileId] = useState<string>('')
  const [campaignPrompt, setCampaignPrompt] = useState(samplePrompt)
  const [campaignId, setCampaignId] = useState<string>('')
  const [campaignStatus, setCampaignStatus] = useState<Record<string, unknown> | null>(null)
  const [campaignJobs, setCampaignJobs] = useState<Array<Record<string, unknown>>>([])
  const [logs, setLogs] = useState<LogLine[]>([])

  useEffect(() => {
    api.health()
      .then((value) => setHealth(value.status))
      .catch(() => setHealth('offline'))
  }, [])

  const stats = useMemo(() => {
    return {
      jobs: campaignJobs.length,
      status: String(campaignStatus?.status ?? 'not started'),
      approval: String(campaignStatus?.execution_mode ?? 'approval_required'),
    }
  }, [campaignJobs.length, campaignStatus])

  const pushLog = (kind: LogLine['kind'], message: string) => setLogs((items) => [{ kind, message }, ...items].slice(0, 12))

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
      const status = await api.campaignStatus(campaignId)
      const jobs = await api.campaignJobs(campaignId)
      setCampaignStatus(status)
      setCampaignJobs(jobs)
      pushLog('info', `Campaign run completed with ${jobs.length} queued jobs`)
    } catch (error) {
      pushLog('error', `Campaign run failed: ${String(error)}`)
    }
  }

  return (
    <main className="shell">
      <header className="topbar">
        <div>
          <h1>Job Copilot</h1>
          <p>Backend-connected job campaign workspace</p>
        </div>
        <div className="health">Backend: {health}</div>
      </header>

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

        <article className="panel">
          <h2>Workflow Status</h2>
          <div className="stat">Campaign status: {stats.status}</div>
          <div className="stat">Approval mode: {stats.approval}</div>
          <div className="stat">Jobs discovered: {stats.jobs}</div>
          <pre className="json">{campaignStatus ? JSON.stringify(campaignStatus, null, 2) : 'No status yet'}</pre>
        </article>

        <article className="panel">
          <h2>Activity Log</h2>
          <ul className="loglist">
            {logs.map((item, index) => (
              <li key={`${item.message}-${index}`} className={item.kind}>
                {item.message}
              </li>
            ))}
          </ul>
        </article>
      </section>

      <section className="panel wide">
        <h2>Queued Jobs</h2>
        <pre className="json">{JSON.stringify(campaignJobs, null, 2)}</pre>
      </section>
    </main>
  )
}

