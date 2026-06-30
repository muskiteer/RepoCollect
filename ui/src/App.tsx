import { useState } from 'react'
import './index.css'
import Home from './Home'
import AddProject from './AddProject'
import BrowseProjects from './BrowseProjects'
import ProjectDetail from './ProjectDetail'
import ChatView from './ChatView'

export type View =
  | 'home'
  | 'add-project'
  | 'browse'
  | 'project-detail'
  | 'chat'

export interface Project {
  id: string
  name: string
  owner: string
  repo: string
  status: 'INDEXED' | 'PENDING' | 'FAILED'
  github: number
  discord: number
  notion: number
  description: string
  lastSync: string
  llm: string
}

export const MOCK_PROJECTS: Project[] = [
  {
    id: 'p1',
    name: 'React',
    owner: 'facebook',
    repo: 'react',
    status: 'INDEXED',
    github: 142,
    discord: 87,
    notion: 23,
    description: 'The library for web and native user interfaces.',
    lastSync: '2 hours ago',
    llm: 'ollama',
  },
  {
    id: 'p2',
    name: 'Cognee',
    owner: 'topoteretes',
    repo: 'cognee',
    status: 'INDEXED',
    github: 318,
    discord: 204,
    notion: 11,
    description: 'Deterministic memory and reasoning for AI agents.',
    lastSync: '45 min ago',
    llm: 'gemini',
  },
  {
    id: 'p3',
    name: 'FastAPI',
    owner: 'tiangolo',
    repo: 'fastapi',
    status: 'PENDING',
    github: 59,
    discord: 0,
    notion: 4,
    description: 'Modern, fast web framework for building APIs with Python.',
    lastSync: 'Ingesting...',
    llm: 'ollama',
  },
  {
    id: 'p4',
    name: 'LangChain',
    owner: 'langchain-ai',
    repo: 'langchain',
    status: 'FAILED',
    github: 0,
    discord: 0,
    notion: 0,
    description: 'Build context-aware reasoning applications.',
    lastSync: 'Failed 1 day ago',
    llm: 'gemini',
  },
]

const NAV_ITEMS = [
  { id: 'home',       label: 'Dashboard',    icon: '⊞' },
  { id: 'browse',     label: 'Projects',     icon: '◫' },
  { id: 'add-project',label: 'Add Project',  icon: '+' },
  { id: 'chat',       label: 'Chat',         icon: '◎' },
]

function App() {
  const [view, setView] = useState<View>('home')
  const [activeProject, setActiveProject] = useState<Project>(MOCK_PROJECTS[0])

  function handleNavigate(v: View, project?: Project) {
    if (project) setActiveProject(project)
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
            <div className="sidebar-version">v0.4.1 · BETA</div>
          </div>
        </aside>

        {/* ── Content ── */}
        <div className="content-area">
          {view === 'home'           && <Home onNavigate={handleNavigate} projects={MOCK_PROJECTS} />}
          {view === 'add-project'    && <AddProject onNavigate={handleNavigate} />}
          {view === 'browse'         && <BrowseProjects onNavigate={handleNavigate} projects={MOCK_PROJECTS} />}
          {view === 'project-detail' && <ProjectDetail onNavigate={handleNavigate} project={activeProject} />}
          {view === 'chat'           && <ChatView onNavigate={handleNavigate} project={activeProject} />}
        </div>
      </div>
    </div>
  )
}

export default App
