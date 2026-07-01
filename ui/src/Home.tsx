import type { View, Project } from './types'

interface Props {
  onNavigate: (view: View, project?: Project) => void
  projects: Project[]
}

const TICKER_ITEMS = [
  'GitHub Ingestion',
  'Discord Sync',
  'Notion Docs',
  'Knowledge Graph',
  'LLM Context',
  'Semantic Search',
  'RAG Pipeline',
  'Vector Store',
  'Open Source',
  'History-Aware AI',
]

const FEATURES = [
  { icon: '⑂',   title: 'GitHub Deep Dive',    desc: 'Issues, PRs, commits, reviews — every thread ingested.' },
  { icon: '💬',  title: 'Discord Threads',     desc: 'Channels, replies, reactions — community knowledge captured.' },
  { icon: '📄',  title: 'Notion Workspaces',   desc: 'Pages, databases, linked mentions — docs in context.' },
  { icon: '⬡',   title: 'Knowledge Graph',     desc: 'Entities, relationships, and timelines — richly linked.' },
]

function StatusBar({ projects }: { projects: Project[] }) {
  const indexed = projects.filter(p => p.status === 'INDEXED').length
  const pending = projects.filter(p => p.status === 'PENDING').length
  const total   = projects.reduce((a, p) => a + p.github + p.discord + p.notion, 0)
  return (
    <div className="stat-grid">
      <div className="stat-cell stat-accent-yellow">
        <div className="stat-label" style={{ color: '#888' }}>Total Projects</div>
        <div className="stat-value">{projects.length}</div>
        <div className="stat-sub" style={{ color: '#888' }}>{indexed} indexed</div>
      </div>
      <div className="stat-cell stat-accent-green">
        <div className="stat-label" style={{ color: '#888' }}>Items Ingested</div>
        <div className="stat-value">{total.toLocaleString()}</div>
        <div className="stat-sub" style={{ color: '#888' }}>across all sources</div>
      </div>
      <div className="stat-cell stat-accent-blue">
        <div className="stat-label" style={{ color: '#888' }}>Pending</div>
        <div className="stat-value">{pending}</div>
        <div className="stat-sub" style={{ color: '#888' }}>in ingestion queue</div>
      </div>
      <div className="stat-cell" style={{ background: '#fff' }}>
        <div className="stat-label">LLM Queries</div>
        <div className="stat-value">—</div>
        <div className="stat-sub">connect to start</div>
      </div>
    </div>
  )
}

export default function Home({ onNavigate, projects }: Props) {
  const tickerArr = [...TICKER_ITEMS, ...TICKER_ITEMS] // duplicate for seamless loop

  return (
    <div>
      {/* ── Hero ── */}
      <div className="hero-band">
        <div className="hero-eyebrow">
          <span>●</span>
          Open-Source Intelligence
        </div>
        <h1 className="hero-title">
          Your project has<br /><span>a memory now.</span>
        </h1>
        <p className="hero-sub">
          Issues, PRs, Discord threads, Notion docs. Repollect builds a
          knowledge graph from your project's entire history — so you can
          ask questions and get answers grounded in real context.
        </p>
        <div className="hero-ctas">
          <button
            id="hero-add"
            className="btn btn-yellow btn-lg"
            onClick={() => onNavigate('add-project')}
          >
            + Add Project
          </button>
          <button
            id="hero-browse"
            className="btn btn-white btn-lg"
            onClick={() => onNavigate('browse')}
          >
            ◫ Browse Projects
          </button>
        </div>
      </div>

      {/* ── Ticker ── */}
      <div className="ticker-bar">
        <div className="ticker-inner">
          {tickerArr.map((item, i) => (
            <span key={i} className="ticker-item">
              <span className="ticker-dot" />
              {item}
            </span>
          ))}
        </div>
      </div>

      {/* ── Page content ── */}
      <div className="page-content">

        {/* Stats */}
        <div className="section-header">
          <h2 className="section-title">Overview</h2>
          <span className="section-meta">Live stats</span>
        </div>
        <StatusBar projects={projects} />

        {/* Recent Projects */}
        <div className="section-header">
          <h2 className="section-title">Recent Projects</h2>
          <button className="btn-ghost" onClick={() => onNavigate('browse')}>
            View all →
          </button>
        </div>
        <hr className="divider" />

        {projects.slice(0, 3).map(p => (
          <MiniProjectRow key={p.id} project={p} onNavigate={onNavigate} />
        ))}

        {/* How it works */}
        <div className="section-header" style={{ marginTop: '40px' }}>
          <h2 className="section-title">How It Works</h2>
        </div>
        <hr className="divider" />

        <div className="steps-row">
          {[
            { num: '01', label: 'Connect Sources',  desc: 'Add a GitHub repo, Discord server, or Notion workspace.' },
            { num: '02', label: 'Cognify',           desc: 'Repollect ingests history into a rich knowledge graph.' },
            { num: '03', label: 'Ask Questions',     desc: 'Chat with an LLM that has full project context.' },
          ].map(s => (
            <div key={s.num} className="step-cell">
              <div className="step-num">{s.num}</div>
              <div className="step-label">{s.label}</div>
              <div className="step-desc">{s.desc}</div>
            </div>
          ))}
        </div>

        {/* Features */}
        <div className="section-header">
          <h2 className="section-title">Sources</h2>
        </div>
        <hr className="divider" />

        <div className="feature-grid">
          {FEATURES.map(f => (
            <div key={f.title} className="feature-cell">
              <div className="feature-icon">{f.icon}</div>
              <div className="feature-title">{f.title}</div>
              <div className="feature-desc">{f.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function MiniProjectRow({ project, onNavigate }: { project: Project; onNavigate: (v: View, p?: Project) => void }) {
  const statusClass = project.status === 'INDEXED' ? 'badge-success'
    : project.status === 'PENDING' ? 'badge-pending'
    : 'badge-danger'

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '14px 20px',
        border: '3px solid #000',
        boxShadow: '4px 4px 0 #000',
        background: '#fff',
        marginBottom: '10px',
        gap: '16px',
        cursor: 'pointer',
        transition: 'transform 70ms, box-shadow 70ms',
      }}
      onClick={() => onNavigate('project-detail', project)}
      onMouseEnter={e => {
        (e.currentTarget as HTMLDivElement).style.transform = 'translate(-2px,-2px)'
        ;(e.currentTarget as HTMLDivElement).style.boxShadow = '6px 6px 0 #000'
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLDivElement).style.transform = ''
        ;(e.currentTarget as HTMLDivElement).style.boxShadow = '4px 4px 0 #000'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flex: 1, minWidth: 0 }}>
        <div style={{
          width: '40px', height: '40px',
          background: '#000', color: '#FFE500',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontWeight: 700, fontSize: '16px', flexShrink: 0,
          border: '2px solid #000',
        }}>
          {project.name[0]}
        </div>
        <div style={{ minWidth: 0 }}>
          <div style={{ fontWeight: 700, fontSize: '15px' }}>{project.name}</div>
          <div style={{ fontSize: '12px', color: '#666', fontFamily: 'monospace' }}>
            {project.owner}/{project.repo}
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexShrink: 0 }}>
        <span style={{ fontSize: '12px', color: '#888', fontWeight: 500 }}>
          {(project.github + project.discord + project.notion).toLocaleString()} items
        </span>
        <span className={`badge ${statusClass}`}>{project.status}</span>
        <button
          className="btn btn-black"
          style={{ fontSize: '11px', padding: '7px 14px' }}
          onClick={e => { e.stopPropagation(); onNavigate('project-detail', project) }}
        >
          View →
        </button>
      </div>
    </div>
  )
}
