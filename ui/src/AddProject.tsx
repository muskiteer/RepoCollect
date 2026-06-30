import { useState } from 'react'
import type { View } from './App'

interface Props {
  onNavigate: (view: View) => void
}

interface FormState {
  projectName: string
  githubOwner: string
  githubRepo: string
  discordGuildIds: string
  llmProvider: string
  notes: string
}

const initial: FormState = {
  projectName: '',
  githubOwner: '',
  githubRepo: '',
  discordGuildIds: '',
  llmProvider: 'ollama',
  notes: '',
}

export default function AddProject({ onNavigate }: Props) {
  const [form, setForm] = useState<FormState>(initial)
  const [status, setStatus] = useState<'idle' | 'loading' | 'done'>('idle')
  const [log, setLog] = useState<string[]>([])

  function set(field: keyof FormState, val: string) {
    setForm(p => ({ ...p, [field]: val }))
  }

  function handleIngest() {
    if (!form.projectName || !form.githubOwner || !form.githubRepo) {
      setLog(['⚠ Please fill in Project Name, GitHub Owner, and Repo.'])
      return
    }
    setStatus('loading')
    const lines = [
      `→ Connecting to github.com/${form.githubOwner}/${form.githubRepo}...`,
      '→ Fetching issues and pull requests...',
      form.discordGuildIds ? `→ Connecting to Discord guilds: ${form.discordGuildIds}` : '→ Discord: skipped (no guild IDs)',
      `→ LLM provider: ${form.llmProvider}`,
      '→ Building knowledge graph...',
      '✓ Ingestion queued. Results will appear in Projects.',
    ]
    setLog([])
    lines.forEach((line, i) => {
      setTimeout(() => {
        setLog(prev => [...prev, line])
        if (i === lines.length - 1) {
          setStatus('done')
          console.log('[REPOLLECT] Ingest payload:', form)
        }
      }, i * 600)
    })
  }

  return (
    <div>
      {/* Top bar */}
      <div className="topbar">
        <span className="topbar-title">Add Project</span>
        <div className="topbar-right">
          <button className="btn-ghost" onClick={() => onNavigate('browse')}>
            ← Back to Projects
          </button>
        </div>
      </div>

      <div className="page-content">
        {/* Title block */}
        <div style={{
          display: 'flex',
          alignItems: 'flex-start',
          gap: '24px',
          marginBottom: '32px',
          flexWrap: 'wrap',
        }}>
          <div style={{
            background: '#FFE500',
            border: '3px solid #000',
            padding: '16px 20px',
            boxShadow: '5px 5px 0 #000',
          }}>
            <div style={{ fontSize: '36px', lineHeight: 1, fontWeight: 700 }}>+</div>
          </div>
          <div>
            <h1 style={{
              fontSize: '28px',
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '-0.01em',
              lineHeight: 1.1,
              marginBottom: '6px',
            }}>
              Add New Project
            </h1>
            <p style={{ fontSize: '14px', color: '#666', maxWidth: '460px', lineHeight: 1.6 }}>
              Connect a GitHub repo, Discord server, or Notion workspace.
              Repollect will ingest all history into a searchable knowledge graph.
            </p>
          </div>
        </div>

        <hr className="divider" />

        {/* Two-column layout */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '28px' }}>
          {/* Left col */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <SectionLabel>Project Identity</SectionLabel>

            <div className="field">
              <label className="field-label" htmlFor="project-name">Project Name *</label>
              <input id="project-name" className="input" placeholder="my-awesome-repo"
                value={form.projectName} onChange={e => set('projectName', e.target.value)} />
            </div>

            <div style={{ display: 'flex', gap: '12px' }}>
              <div className="field" style={{ flex: 1 }}>
                <label className="field-label" htmlFor="github-owner">GitHub Owner *</label>
                <input id="github-owner" className="input" placeholder="facebook"
                  value={form.githubOwner} onChange={e => set('githubOwner', e.target.value)} />
              </div>
              <div className="field" style={{ flex: 1 }}>
                <label className="field-label" htmlFor="github-repo">Repo Name *</label>
                <input id="github-repo" className="input" placeholder="react"
                  value={form.githubRepo} onChange={e => set('githubRepo', e.target.value)} />
              </div>
            </div>

            {/* Repo preview */}
            {(form.githubOwner || form.githubRepo) && (
              <div style={{
                background: '#000', color: '#FFE500',
                padding: '10px 14px', fontSize: '13px',
                fontFamily: 'monospace', border: '3px solid #000',
                boxShadow: '3px 3px 0 #FFE500',
              }}>
                ⑂ github.com/{form.githubOwner || '<owner>'}/{form.githubRepo || '<repo>'}
              </div>
            )}

            <SectionLabel>LLM Config</SectionLabel>

            <div className="field">
              <label className="field-label" htmlFor="llm-provider">LLM Provider</label>
              <select id="llm-provider" className="select"
                value={form.llmProvider} onChange={e => set('llmProvider', e.target.value)}>
                <option value="ollama">Ollama (local)</option>
                <option value="gemini">Gemini</option>
              </select>
              <span className="field-hint">
                {form.llmProvider === 'ollama'
                  ? 'Make sure Ollama is running on :11434'
                  : 'Requires GEMINI_API_KEY in .env'}
              </span>
            </div>
          </div>

          {/* Right col */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
            <SectionLabel>Optional Sources</SectionLabel>

            <div className="field">
              <label className="field-label" htmlFor="discord-guilds">
                Discord Guild IDs
                <span style={{ color: '#aaa', fontWeight: 400, marginLeft: '6px', textTransform: 'none', fontSize: '10px' }}>optional</span>
              </label>
              <input id="discord-guilds" className="input"
                placeholder="123456789, 987654321"
                value={form.discordGuildIds} onChange={e => set('discordGuildIds', e.target.value)} />
              <span className="field-hint">Comma-separated. Leave blank to skip Discord.</span>
            </div>

            <div className="field">
              <label className="field-label" htmlFor="notes">Context Notes</label>
              <textarea id="notes" className="textarea" rows={5}
                placeholder="Any context about this project — what it does, key contributors, important threads..."
                value={form.notes} onChange={e => set('notes', e.target.value)} />
            </div>

            {/* Checklist */}
            <div style={{
              border: '3px solid #000',
              boxShadow: '4px 4px 0 #000',
              overflow: 'hidden',
            }}>
              <div style={{
                background: '#000', color: '#FFE500',
                padding: '8px 14px',
                fontSize: '10px', fontWeight: 700,
                letterSpacing: '0.12em', textTransform: 'uppercase',
              }}>
                Pre-flight Checklist
              </div>
              {[
                { ok: !!form.projectName,    text: 'Project name set' },
                { ok: !!form.githubOwner,    text: 'GitHub owner set' },
                { ok: !!form.githubRepo,     text: 'GitHub repo set' },
                { ok: form.llmProvider !== '',text: 'LLM provider selected' },
              ].map((c, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: '10px',
                  padding: '9px 14px',
                  borderTop: i > 0 ? '2px solid #eee' : 'none',
                  fontSize: '12px', fontWeight: 500,
                }}>
                  <span style={{ color: c.ok ? '#00E5A0' : '#ccc', fontSize: '14px', fontWeight: 700 }}>
                    {c.ok ? '✓' : '○'}
                  </span>
                  <span style={{ color: c.ok ? '#000' : '#aaa' }}>{c.text}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Ingest button */}
        <button
          id="ingest-btn"
          className="btn btn-black btn-full"
          style={{ letterSpacing: '0.1em', opacity: status === 'loading' ? 0.7 : 1 }}
          onClick={handleIngest}
          disabled={status === 'loading'}
        >
          {status === 'loading'
            ? '⟳  Ingesting...'
            : status === 'done'
            ? '✓  Queued — View in Projects'
            : 'INGEST PROJECT →'}
        </button>

        {/* Log box */}
        <div style={{ marginTop: '16px' }}>
          <div style={{
            fontSize: '10px', fontWeight: 700,
            letterSpacing: '0.12em', textTransform: 'uppercase',
            color: '#999', marginBottom: '8px',
          }}>
            Ingestion Log
          </div>
          <div className="status-box" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '4px', minHeight: '110px' }}>
            {log.length === 0
              ? 'Ingestion results will appear here...'
              : log.map((line, i) => (
                  <div key={i} style={{
                    color: line.startsWith('✓') ? '#00E5A0'
                         : line.startsWith('⚠') ? '#FF3B00'
                         : '#444',
                    fontWeight: line.startsWith('✓') || line.startsWith('⚠') ? 700 : 400,
                  }}>
                    {line}
                  </div>
                ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      fontSize: '10px',
      fontWeight: 700,
      letterSpacing: '0.14em',
      textTransform: 'uppercase',
      color: '#000',
      borderBottom: '2px solid #000',
      paddingBottom: '6px',
    }}>
      {children}
    </div>
  )
}
