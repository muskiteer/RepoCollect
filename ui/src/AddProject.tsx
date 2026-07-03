import { useState } from 'react'
import type { View } from './types'

interface Props {
  onNavigate: (view: View) => void
}

interface FormState {
  projectName: string
  githubOwner: string
  githubRepo: string
  githubToken: string
  notionToken: string
  discordToken: string
  discordGuildIds: string
  llmProvider: string
  notes: string
}

const initial: FormState = {
  projectName: '',
  githubOwner: '',
  githubRepo: '',
  githubToken: '',
  notionToken: '',
  discordToken: '',
  discordGuildIds: '',
  llmProvider: 'ollama',
  notes: '',
}

export default function AddProject({ onNavigate }: Props) {
  const [form, setForm] = useState<FormState>(initial)
  const [status, setStatus] = useState<'idle' | 'loading' | 'done'>('idle')
  const [log, setLog] = useState<string[]>([])
  const [files, setFiles] = useState<File[]>([])

  function set(field: keyof FormState, val: string) {
    setForm(p => ({ ...p, [field]: val }))
  }

  async function handleIngest() {
    if (!form.projectName || !form.githubOwner || !form.githubRepo || !form.githubToken) {
      setLog(['⚠ Please fill in Project Name, GitHub Owner, Repo, and GitHub Token.'])
      return
    }
    setStatus('loading')
    setLog(['→ Contacting API and validating tokens...'])
    
    try {
      const res = await fetch('/api/v1/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          repo_owner: form.githubOwner,
          repo_name: form.githubRepo,
          dataset: form.projectName,
          github_token: form.githubToken,
          notion_token: form.notionToken || undefined,
          discord_token: form.discordToken || undefined
        })
      })
      
      const data = await res.json()
      
      if (!res.ok) {
        throw new Error(data.detail || 'Failed to create project')
      }
      
      setLog(prev => [...prev, `✓ Auth verified. Project ${data.id} created successfully!`])

      // Upload files if any
      if (files.length > 0) {
        setLog(prev => [...prev, `→ Uploading ${files.length} file(s)...`])
        const formData = new FormData()
        files.forEach(f => formData.append('files', f))
        const uploadRes = await fetch(`/api/v1/files/${encodeURIComponent(form.projectName)}/upload`, {
          method: 'POST',
          body: formData
        })
        if (!uploadRes.ok) {
          throw new Error('Failed to upload files')
        }
        const uploadData = await uploadRes.json()
        setLog(prev => [...prev, `✓ ${uploadData.uploaded} file(s) uploaded.`])
      }

      setLog(prev => [...prev, '→ Starting background ingestion...'])
      
      const ingestRes = await fetch(`/api/v1/projects/${data.id}/ingest`, { method: 'POST' })
      if (!ingestRes.ok) {
        throw new Error('Failed to start ingestion')
      }

      setLog(prev => [...prev, '✓ Ingestion queued. Returning to projects view...'])
      setStatus('done')
      setTimeout(() => {
        onNavigate('browse')
      }, 1000)
      
    } catch (e: any) {
      console.error(e)
      setLog(prev => [...prev, `⚠ Error: ${e.message}`])
      setStatus('idle')
    }
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
              <label className="field-label" htmlFor="project-name">Project Name (Dataset) *</label>
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

            <div className="field">
              <label className="field-label" htmlFor="github-token">GitHub Token *</label>
              <input id="github-token" className="input" type="password" placeholder="ghp_..."
                value={form.githubToken} onChange={e => set('githubToken', e.target.value)} />
              <span className="field-hint">Required. Token will be validated instantly.</span>
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
              <label className="field-label" htmlFor="notion-token">
                Notion Integration Token
                <span style={{ color: '#aaa', fontWeight: 400, marginLeft: '6px', textTransform: 'none', fontSize: '10px' }}>optional</span>
              </label>
              <input id="notion-token" className="input" type="password"
                placeholder="secret_..."
                value={form.notionToken} onChange={e => set('notionToken', e.target.value)} />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="discord-token">
                Discord Bot Token
                <span style={{ color: '#aaa', fontWeight: 400, marginLeft: '6px', textTransform: 'none', fontSize: '10px' }}>optional</span>
              </label>
              <input id="discord-token" className="input" type="password"
                placeholder="MTE..."
                value={form.discordToken} onChange={e => set('discordToken', e.target.value)} />
            </div>

            <div className="field">
              <label className="field-label" htmlFor="discord-guilds">
                Discord Guild IDs
                <span style={{ color: '#aaa', fontWeight: 400, marginLeft: '6px', textTransform: 'none', fontSize: '10px' }}>optional</span>
              </label>
              <input id="discord-guilds" className="input"
                placeholder="123456789, 987654321"
                value={form.discordGuildIds} onChange={e => set('discordGuildIds', e.target.value)} />
            </div>

            <SectionLabel>Upload Files</SectionLabel>

            <div className="field">
              <label className="field-label">
                Local Documents
                <span style={{ color: '#aaa', fontWeight: 400, marginLeft: '6px', textTransform: 'none', fontSize: '10px' }}>optional · PDF, MD, TXT</span>
              </label>
              <div
                style={{
                  border: '3px dashed #ccc',
                  padding: '20px',
                  textAlign: 'center',
                  cursor: 'pointer',
                  background: files.length > 0 ? '#f0fdf4' : '#fafafa',
                  transition: 'background 0.2s',
                }}
                onClick={() => document.getElementById('file-upload')?.click()}
                onDragOver={e => { e.preventDefault(); e.stopPropagation(); }}
                onDrop={e => {
                  e.preventDefault();
                  e.stopPropagation();
                  const dropped = Array.from(e.dataTransfer.files).filter(f =>
                    /\.(pdf|md|txt)$/i.test(f.name)
                  );
                  setFiles(prev => [...prev, ...dropped]);
                }}
              >
                <input
                  id="file-upload"
                  type="file"
                  multiple
                  accept=".pdf,.md,.txt"
                  style={{ display: 'none' }}
                  onChange={e => {
                    if (e.target.files) {
                      setFiles(prev => [...prev, ...Array.from(e.target.files!)]);
                    }
                  }}
                />
                <div style={{ fontSize: '24px', color: '#ccc', marginBottom: '6px' }}>📄</div>
                <div style={{ fontSize: '12px', fontWeight: 600, color: '#888' }}>
                  {files.length > 0
                    ? `${files.length} file(s) selected`
                    : 'Drop files here or click to browse'}
                </div>
              </div>
              {files.length > 0 && (
                <div style={{ marginTop: '8px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  {files.map((f, i) => (
                    <div key={i} style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                      fontSize: '11px', padding: '4px 8px',
                      border: '1px solid #eee', background: '#fafafa',
                    }}>
                      <span style={{ fontWeight: 600 }}>{f.name}</span>
                      <button
                        style={{ background: 'none', border: 'none', color: '#FF3B00', cursor: 'pointer', fontWeight: 700, fontSize: '13px' }}
                        onClick={e => { e.stopPropagation(); setFiles(prev => prev.filter((_, j) => j !== i)); }}
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              )}
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
                { ok: !!form.githubOwner && !!form.githubRepo, text: 'GitHub repo set' },
                { ok: !!form.githubToken,    text: 'GitHub token provided' },
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
            ? '⟳  Validating...'
            : status === 'done'
            ? '✓  Created — Redirecting'
            : 'CREATE PROJECT →'}
        </button>

        {/* Log box */}
        <div style={{ marginTop: '16px' }}>
          <div style={{
            fontSize: '10px', fontWeight: 700,
            letterSpacing: '0.12em', textTransform: 'uppercase',
            color: '#999', marginBottom: '8px',
          }}>
            Creation Log
          </div>
          <div className="status-box" style={{ flexDirection: 'column', alignItems: 'flex-start', gap: '4px', minHeight: '110px' }}>
            {log.length === 0
              ? 'Results will appear here...'
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
