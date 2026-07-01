import { useState, useEffect } from 'react'
import './index.css'
import Home from './Home'
import AddProject from './AddProject'
import BrowseProjects from './BrowseProjects'
import ProjectDetail from './ProjectDetail'
import ChatView from './ChatView'

import type { View, Project } from './types'


const NAV_ITEMS = [
  { id: 'home',       label: 'Dashboard',    icon: '⊞' },
  { id: 'browse',     label: 'Projects',     icon: '◫' },
  { id: 'add-project',label: 'Add Project',  icon: '+' },
  { id: 'chat',       label: 'Chat',         icon: '◎' },
]

function App() {
  const [view, setView] = useState<View>('home')
  const [activeProject, setActiveProject] = useState<Project | undefined>()
  const [projects, setProjects] = useState<Project[]>([])

  const fetchProjects = async () => {
    try {
      const res = await fetch('/api/v1/projects')
      const data = await res.json()
      const mapped = data.map((d: any) => ({
        id: d.id,
        name: d.repo_name,
        owner: d.repo_owner,
        repo: d.repo_name,
        status: d.status || 'PENDING',
        github: 1, 
        discord: 0,
        notion: 0,
        description: `Dataset: ${d.dataset}`,
        lastSync: d.last_synced_at ? new Date(d.last_synced_at).toLocaleString() : 'Never',
        llm: 'ollama'
      }))
      setProjects(prev => {
        prev.forEach(p => {
          const next = mapped.find((n: any) => n.id === p.id)
          if (next && p.status === 'SYNCING') {
            if (next.status === 'INDEXED') {
              alert(`Sync completed for ${p.name}!`)
            } else if (next.status === 'FAILED') {
              alert(`Sync failed for ${p.name}.`)
            }
          }
        })
        return mapped
      })
      setActiveProject(prev => prev ? (mapped.find((p: any) => p.id === prev.id) || prev) : prev)
    } catch (e) {
      console.error('Failed to fetch projects', e)
    }
  }

  useEffect(() => {
    fetchProjects()
    const interval = setInterval(fetchProjects, 5000)
    return () => clearInterval(interval)
  }, [])

  function handleNavigate(v: View, project?: Project) {
    if (project) setActiveProject(project)
    if (v === 'browse') fetchProjects()
    setView(v)
  }

  return (
    <div className="app-shell">
      <div className="main-layout">
        {/* ── Sidebar ── */}
        <aside className="sidebar">
          <div className="sidebar-logo">
            <span className="sidebar-wordmark">Repollect</span>
            <span className="sidebar-tagline">Knowledge Ingestion Tool</span>
          </div>

          <nav className="sidebar-nav">
            <div className="nav-section-label">Navigate</div>
            {NAV_ITEMS.map(item => (
              <button
                key={item.id}
                id={`nav-${item.id}`}
                className={`nav-item ${view === item.id || (view === 'project-detail' && item.id === 'browse') ? 'active' : ''}`}
                onClick={() => setView(item.id as View)}
              >
                <span className="nav-item-icon">{item.icon}</span>
                {item.label}
              </button>
            ))}
          </nav>

          <div className="sidebar-footer">
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
              <div style={{
                width: '8px', height: '8px',
                background: '#00E5A0',
                border: '2px solid #333',
                borderRadius: '50%',
              }} />
              <span style={{ fontSize: '10px', color: '#555', fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
                Backend Live
              </span>
            </div>
            <div className="sidebar-version" style={{ marginBottom: '8px' }}>v0.4.1 · BETA</div>
            <div className="sidebar-author" style={{ 
              fontSize: '10px', 
              color: '#888', 
              fontWeight: 700,
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              borderTop: '2px dashed #333',
              paddingTop: '8px',
              marginTop: '8px'
            }}>
              Made by <span style={{ color: '#FFE500' }}>Vansh</span> aka <span style={{ color: '#FFE500' }}>muskiteer</span>
            </div>
          </div>
        </aside>

        {/* ── Content ── */}
        <div className="content-area">
          {view === 'home'           && <Home onNavigate={handleNavigate} projects={projects} />}
          {view === 'add-project'    && <AddProject onNavigate={handleNavigate} />}
          {view === 'browse'         && <BrowseProjects onNavigate={handleNavigate} projects={projects} />}
          {view === 'project-detail' && activeProject && <ProjectDetail onNavigate={handleNavigate} project={activeProject} />}
          {view === 'chat'           && activeProject && <ChatView onNavigate={handleNavigate} project={activeProject} />}
        </div>
      </div>
    </div>
  )
}

export default App
