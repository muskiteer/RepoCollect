import type { View, Project } from './App'

interface Props {
  onNavigate: (view: View, project?: Project) => void
  project: Project
}

const ACTIVITY = [
  { dot: 'activity-dot-green',  text: 'PR #2847 merged: "Add concurrent rendering"',       time: '2h ago' },
  { dot: 'activity-dot-blue',   text: 'Issue #2901 opened: "Suspense boundary leak"',       time: '5h ago' },
  { dot: 'activity-dot-yellow', text: 'Discord: 14 new messages in #contributors',          time: '8h ago' },
  { dot: 'activity-dot-green',  text: 'Notion: "Roadmap Q3 2026" page updated',             time: '1d ago' },
  { dot: 'activity-dot-blue',   text: 'PR #2844 review: "useTransition performance pass"', time: '1d ago' },
  { dot: 'activity-dot-red',    text: 'Issue #2899 closed: wontfix — "Server components"',  time: '2d ago' },
]

export default function ProjectDetail({ onNavigate, project }: Props) {
  const total = project.github + project.discord + project.notion
  const statusColor = project.status === 'INDEXED' ? '#00E5A0'
                    : project.status === 'PENDING' ? '#FFE500'
                    : '#FF3B00'

  return (
    <div>
      {/* Topbar */}
      <div className="topbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button className="btn-ghost" style={{ fontSize: '12px' }} onClick={() => onNavigate('browse')}>
            ← Projects
          </button>
          <span style={{ color: '#ccc' }}>/</span>
          <span className="topbar-title">{project.name}</span>
        </div>
        <div className="topbar-right">
          <button
            id="detail-chat-btn"
            className="btn btn-black"
            style={{ fontSize: '12px', padding: '8px 16px' }}
            onClick={() => onNavigate('chat', project)}
            disabled={project.status !== 'INDEXED'}
          >
            Chat with {project.name} →
          </button>
        </div>
      </div>

      {/* Hero band */}
      <div className="detail-hero">
        {/* Top row */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '24px', flexWrap: 'wrap', marginBottom: '24px' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px', flexWrap: 'wrap' }}>
              <h1 style={{ fontSize: '36px', fontWeight: 700, letterSpacing: '-0.02em', color: '#fff', lineHeight: 1 }}>
                {project.name}
              </h1>
              <span
                className={`badge ${project.status === 'INDEXED' ? 'badge-success' : project.status === 'PENDING' ? 'badge-pending' : 'badge-danger'}`}
                style={{ fontSize: '11px', padding: '4px 10px' }}
              >
                {project.status}
              </span>
              <span style={{
                border: '2px solid #444',
                padding: '4px 10px',
                fontSize: '10px',
                fontWeight: 700,
                letterSpacing: '0.1em',
                color: '#888',
                textTransform: 'uppercase',
              }}>
                {project.llm}
              </span>
            </div>
            <div style={{ fontFamily: 'monospace', fontSize: '15px', color: '#888', marginBottom: '10px' }}>
              github.com/{project.owner}/{project.repo}
            </div>
            <p style={{ fontSize: '14px', color: '#aaa', maxWidth: '480px', lineHeight: 1.6 }}>
              {project.description}
            </p>
          </div>

          {/* Donut-style breakdown */}
          <div style={{
            border: '3px solid #333',
            background: '#111',
            padding: '20px',
            minWidth: '180px',
            boxShadow: '5px 5px 0 #FFE500',
          }}>
            <div style={{ fontSize: '10px', color: '#555', letterSpacing: '0.12em', textTransform: 'uppercase', marginBottom: '12px', fontWeight: 700 }}>
              Item Breakdown
            </div>
            {[
              { label: 'GitHub',  val: project.github,  color: '#0057FF' },
              { label: 'Discord', val: project.discord, color: '#7289DA' },
              { label: 'Notion',  val: project.notion,  color: '#fff' },
            ].map(s => (
              <div key={s.label} style={{ marginBottom: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#888', marginBottom: '4px' }}>
                  <span style={{ color: '#ccc', fontWeight: 600 }}>{s.label}</span>
                  <span style={{ color: s.color, fontWeight: 700 }}>{s.val}</span>
                </div>
                <div style={{ height: '5px', background: '#222', border: '1px solid #333' }}>
                  <div style={{
                    height: '100%',
                    background: s.color,
                    width: total > 0 ? `${(s.val / total) * 100}%` : '0%',
                    transition: 'width 600ms ease',
                  }} />
                </div>
              </div>
            ))}
            <div style={{
              marginTop: '12px',
              paddingTop: '10px',
              borderTop: '1px solid #333',
              fontSize: '12px',
              fontWeight: 700,
              color: statusColor,
            }}>
              {total.toLocaleString()} total items
            </div>
          </div>
        </div>

        {/* Stats row */}
        <div style={{ display: 'flex', gap: '0', flexWrap: 'wrap' }}>
          {[
            { label: 'Last Sync',   val: project.lastSync, mono: false },
            { label: 'GitHub Items', val: project.github.toString(), mono: true },
            { label: 'Discord Msgs', val: project.discord.toString(), mono: true },
            { label: 'Notion Pages', val: project.notion.toString(), mono: true },
          ].map((s, i) => (
            <div key={i} style={{
              padding: '12px 24px 12px 0',
              marginRight: '24px',
              borderRight: i < 3 ? '1px solid #333' : 'none',
              paddingRight: '24px',
            }}>
              <div style={{ fontSize: '9px', color: '#555', letterSpacing: '0.12em', textTransform: 'uppercase', fontWeight: 700, marginBottom: '4px' }}>
                {s.label}
              </div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: '#fff', fontFamily: s.mono ? 'monospace' : 'inherit' }}>
                {s.val}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="page-content">
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '28px' }}>
          {/* Recent Activity */}
          <div>
            <div className="section-header">
              <h2 className="section-title" style={{ fontSize: '18px' }}>Recent Activity</h2>
              <span className="section-meta">Last 7 days</span>
            </div>
            <hr className="divider" />
            {ACTIVITY.map((a, i) => (
              <div key={i} className="activity-row">
                <div className={`activity-dot ${a.dot}`} />
                <div className="activity-text">{a.text}</div>
                <div className="activity-time">{a.time}</div>
              </div>
            ))}
          </div>

          {/* Right panel */}
          <div>
            {/* Actions */}
            <div className="section-header">
              <h2 className="section-title" style={{ fontSize: '18px' }}>Actions</h2>
            </div>
            <hr className="divider" />

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '28px' }}>
              <button
                className="btn btn-black btn-full"
                onClick={() => onNavigate('chat', project)}
                disabled={project.status !== 'INDEXED'}
              >
                ◎ Start Chat Session
              </button>
              <button
                className="btn btn-yellow btn-full"
                onClick={() => alert('Re-sync triggered (API coming soon)')}
              >
                ⟳ Re-sync Sources
              </button>
              <button
                className="btn btn-white btn-full"
                onClick={() => onNavigate('add-project')}
              >
                ✎ Edit Configuration
              </button>
              <button
                className="btn btn-danger btn-full"
                onClick={() => confirm('Delete this project?') && onNavigate('browse')}
              >
                ✕ Delete Project
              </button>
            </div>

            {/* Source config */}
            <div className="section-header">
              <h2 className="section-title" style={{ fontSize: '18px' }}>Source Config</h2>
            </div>
            <hr className="divider" />

            {[
              { icon: '⑂', label: 'GitHub',  val: `${project.owner}/${project.repo}`, ok: true },
              { icon: '💬', label: 'Discord', val: project.discord > 0 ? 'Guilds connected' : 'Not connected', ok: project.discord > 0 },
              { icon: '📄', label: 'Notion',  val: project.notion > 0 ? 'Workspace linked' : 'Not connected', ok: project.notion > 0 },
            ].map(s => (
              <div key={s.label} style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '12px 14px',
                border: '2px solid #000',
                boxShadow: '3px 3px 0 #000',
                marginBottom: '8px',
                background: '#fff',
              }}>
                <span style={{ fontSize: '18px', width: '22px', textAlign: 'center' }}>{s.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.08em' }}>{s.label}</div>
                  <div style={{ fontSize: '12px', color: '#666', fontFamily: 'monospace' }}>{s.val}</div>
                </div>
                <span style={{ color: s.ok ? '#00E5A0' : '#ccc', fontWeight: 700, fontSize: '16px' }}>
                  {s.ok ? '✓' : '○'}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
