import type { View, Project } from './App'

interface Props {
  onNavigate: (view: View, project?: Project) => void
  projects: Project[]
}

function StatusBadge({ status }: { status: Project['status'] }) {
  const cls = status === 'INDEXED' ? 'badge-success'
            : status === 'PENDING' ? 'badge-pending'
            : 'badge-danger'
  return <span className={`badge ${cls}`}>{status}</span>
}

export default function BrowseProjects({ onNavigate, projects }: Props) {
  const indexed = projects.filter(p => p.status === 'INDEXED').length
  const totalItems = projects.reduce((a, p) => a + p.github + p.discord + p.notion, 0)

  return (
    <div>
      {/* Top bar */}
      <div className="topbar">
        <span className="topbar-title">Projects</span>
        <div className="topbar-right">
          <span style={{ fontSize: '12px', color: '#666', fontWeight: 600 }}>
            {indexed}/{projects.length} indexed · {totalItems.toLocaleString()} items total
          </span>
          <button
            id="add-project-from-browse"
            className="btn btn-black"
            style={{ fontSize: '12px', padding: '8px 14px' }}
            onClick={() => onNavigate('add-project')}
          >
            + Add Project
          </button>
        </div>
      </div>

      <div className="page-content">
        <div className="section-header">
          <h1 className="section-title">Your Projects</h1>
          <span className="section-meta">{projects.length} total</span>
        </div>
        <hr className="divider" />

        {/* Filter strip */}
        <div style={{
          display: 'flex',
          gap: '8px',
          marginBottom: '24px',
          flexWrap: 'wrap',
        }}>
          {['All', 'Indexed', 'Pending', 'Failed'].map(f => (
            <button
              key={f}
              className="btn btn-white"
              style={{
                fontSize: '11px',
                padding: '6px 14px',
                background: f === 'All' ? '#000' : '#fff',
                color: f === 'All' ? '#FFE500' : '#000',
              }}
            >
              {f}
            </button>
          ))}
        </div>

        {/* Project cards */}
        {projects.map(project => (
          <div key={project.id} className="project-card">
            {/* Accent stripe */}
            <div style={{
              height: '6px',
              background: project.status === 'INDEXED' ? '#00E5A0'
                        : project.status === 'PENDING' ? '#FFE500'
                        : '#FF3B00',
              borderBottom: '3px solid #000',
            }} />

            <div className="project-card-header">
              {/* Left */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '4px', flexWrap: 'wrap' }}>
                  <span className="project-name">{project.name}</span>
                  <StatusBadge status={project.status} />
                  <span style={{
                    fontSize: '10px',
                    border: '2px solid #ccc',
                    padding: '2px 7px',
                    color: '#888',
                    fontWeight: 700,
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                  }}>
                    {project.llm}
                  </span>
                </div>
                <div className="project-repo">{project.owner}/{project.repo}</div>
                <div style={{ fontSize: '12px', color: '#555', marginTop: '6px', lineHeight: 1.5 }}>
                  {project.description}
                </div>
              </div>

              {/* Right actions */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'flex-end', flexShrink: 0 }}>
                <button
                  id={`view-${project.id}`}
                  className="btn btn-black"
                  style={{ fontSize: '11px', padding: '8px 16px' }}
                  onClick={() => onNavigate('project-detail', project)}
                >
                  VIEW →
                </button>
                <button
                  id={`chat-${project.id}`}
                  className="btn btn-yellow"
                  style={{ fontSize: '11px', padding: '8px 16px' }}
                  onClick={() => onNavigate('chat', project)}
                  disabled={project.status !== 'INDEXED'}
                >
                  CHAT →
                </button>
              </div>
            </div>

            {/* Body: stats */}
            <div className="project-card-body">
              <div className="stat-pills">
                <div className="stat-pill">
                  <span>⑂</span>
                  <span className="stat-pill-val">{project.github}</span>
                  <span>GitHub items</span>
                </div>
                <div className="stat-pill">
                  <span>💬</span>
                  <span className="stat-pill-val">{project.discord}</span>
                  <span>Discord msgs</span>
                </div>
                <div className="stat-pill">
                  <span>📄</span>
                  <span className="stat-pill-val">{project.notion}</span>
                  <span>Notion pages</span>
                </div>
              </div>

              <div style={{ fontSize: '11px', color: '#999', fontWeight: 500, textAlign: 'right', flexShrink: 0 }}>
                Synced: {project.lastSync}
              </div>
            </div>
          </div>
        ))}

        {/* Empty add card */}
        <div
          style={{
            border: '3px dashed #ccc',
            padding: '32px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '14px',
            cursor: 'pointer',
            marginTop: '4px',
          }}
          onClick={() => onNavigate('add-project')}
        >
          <div style={{ fontSize: '32px', color: '#ccc' }}>+</div>
          <div style={{ fontSize: '13px', fontWeight: 700, color: '#aaa', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Add a new project
          </div>
        </div>
      </div>
    </div>
  )
}
