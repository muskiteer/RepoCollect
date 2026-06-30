import { useState, useRef, useEffect } from 'react'
import type { View, Project } from './App'

interface Props {
  onNavigate: (view: View, project?: Project) => void
  project: Project
}

interface Message {
  role: 'user' | 'ai'
  text: string
  ts: string
}

const SEED_MESSAGES: Message[] = [
  {
    role: 'ai',
    text: `Hey! I've ingested **${'{project}'}** — ${'{total}'} items across GitHub, Discord, and Notion. Ask me anything about the project history, contributors, or recent decisions.`,
    ts: 'now',
  },
]

const SUGGESTED = [
  'What are the most discussed open issues?',
  'Who are the top contributors in the last 90 days?',
  'Summarize the latest PR decisions',
  'What did the team discuss about performance?',
  'Which Discord threads mention breaking changes?',
]

const AI_REPLIES: Record<string, string> = {
  default:
    'Based on the ingested data, I can see several relevant discussions and commits related to your question. The knowledge graph links 47 related items — would you like me to dive deeper into any specific area?',
  contributors:
    'Top contributors over the last 90 days: **@gaearon** (42 commits, 18 PRs merged), **@sebmarkbage** (29 commits), **@acdlite** (24 commits). Community contributors accounted for 31% of all merged PRs.',
  issues:
    'The 5 most-discussed open issues by comment count: #2901 "Suspense boundary leak" (87 comments), #2887 "useEffect double-fire in strict mode" (64 comments), #2856 "Hydration mismatch warnings" (58 comments).',
  performance:
    'Performance was discussed in 23 Discord threads and 12 GitHub issues. Key themes: concurrent rendering overhead in deep trees (Issue #2834), and a proposal to cache reconciler intermediate states (PR #2812, now merged).',
}

function getReply(msg: string): string {
  const lower = msg.toLowerCase()
  if (lower.includes('contribut')) return AI_REPLIES.contributors
  if (lower.includes('issue') || lower.includes('discuss')) return AI_REPLIES.issues
  if (lower.includes('perform') || lower.includes('speed')) return AI_REPLIES.performance
  return AI_REPLIES.default
}

function fmtTime(d: Date) {
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

export default function ChatView({ onNavigate, project }: Props) {
  const total = project.github + project.discord + project.notion
  const [messages, setMessages] = useState<Message[]>(() =>
    SEED_MESSAGES.map(m => ({
      ...m,
      text: m.text
        .replace('{project}', project.name)
        .replace('{total}', total.toLocaleString()),
    }))
  )
  const [input, setInput] = useState('')
  const [thinking, setThinking] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, thinking])

  function send(text?: string) {
    const msg = (text ?? input).trim()
    if (!msg || thinking) return
    const now = fmtTime(new Date())
    setMessages(prev => [...prev, { role: 'user', text: msg, ts: now }])
    setInput('')
    setThinking(true)
    setTimeout(() => {
      setThinking(false)
      setMessages(prev => [...prev, {
        role: 'ai',
        text: getReply(msg),
        ts: fmtTime(new Date()),
      }])
    }, 1200 + Math.random() * 600)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Topbar */}
      <div className="topbar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button className="btn-ghost" style={{ fontSize: '12px' }} onClick={() => onNavigate('project-detail', project)}>
            ← {project.name}
          </button>
          <span style={{ color: '#ccc' }}>/</span>
          <span className="topbar-title">Chat</span>
        </div>
        <div className="topbar-right">
          <div style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            border: '2px solid #000', padding: '5px 12px',
            fontSize: '11px', fontWeight: 700, letterSpacing: '0.08em',
            textTransform: 'uppercase', background: '#fff',
            boxShadow: '2px 2px 0 #000',
          }}>
            <span style={{ width: '7px', height: '7px', background: '#00E5A0', borderRadius: '50%', border: '1px solid #000', display: 'inline-block' }} />
            {project.llm} · {total} items
          </div>
          <button
            className="btn btn-white"
            style={{ fontSize: '11px', padding: '7px 14px' }}
            onClick={() => setMessages(SEED_MESSAGES.map(m => ({
              ...m,
              text: m.text.replace('{project}', project.name).replace('{total}', total.toLocaleString()),
            })))}
          >
            Clear
          </button>
        </div>
      </div>

      {/* Main chat layout */}
      <div className="chat-layout" style={{ flex: 1, border: 'none', borderTop: '4px solid #000' }}>
        {/* Messages */}
        <div className="chat-main">
          <div className="chat-messages">
            {messages.map((m, i) => (
              <div key={i} className={`chat-bubble chat-bubble-${m.role}`}>
                <div className="chat-bubble-label">
                  {m.role === 'user' ? 'You' : `${project.name} AI`} · {m.ts}
                </div>
                <div className={`bubble-text ${m.role === 'user' ? 'bubble-user' : 'bubble-ai'}`}>
                  {m.text.split('**').map((part, j) =>
                    j % 2 === 1 ? <strong key={j}>{part}</strong> : part
                  )}
                </div>
              </div>
            ))}

            {thinking && (
              <div className="chat-bubble chat-bubble-ai">
                <div className="chat-bubble-label">{project.name} AI · now</div>
                <div className="bubble-text bubble-ai" style={{ display: 'flex', gap: '5px', alignItems: 'center' }}>
                  <ThinkingDots />
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input bar */}
          <div className="chat-input-bar">
            <input
              id="chat-input"
              className="input"
              placeholder={`Ask anything about ${project.name}...`}
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && send()}
            />
            <button
              id="chat-send"
              className="chat-send-btn"
              onClick={() => send()}
              disabled={!input.trim() || thinking}
            >
              SEND →
            </button>
          </div>
        </div>

        {/* Sidebar */}
        <div className="chat-sidebar">
          <div className="chat-sidebar-section">
            <div className="chat-sidebar-title">Knowledge Sources</div>
            {[
              { icon: '⑂', label: 'GitHub',  count: project.github },
              { icon: '💬', label: 'Discord', count: project.discord },
              { icon: '📄', label: 'Notion',  count: project.notion },
            ].map(s => (
              <div key={s.label} className="source-chip">
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="source-chip-icon">{s.icon}</span>
                  <span>{s.label}</span>
                </div>
                <span className="source-chip-count">{s.count} items</span>
              </div>
            ))}
          </div>

          <div className="chat-sidebar-section">
            <div className="chat-sidebar-title">Suggested Questions</div>
            {SUGGESTED.map((q, i) => (
              <button
                key={i}
                id={`suggested-${i}`}
                className="suggested-chip"
                onClick={() => send(q)}
              >
                {q}
              </button>
            ))}
          </div>

          <div className="chat-sidebar-section">
            <div className="chat-sidebar-title">Session Info</div>
            <div style={{ fontSize: '11px', color: '#888', lineHeight: 1.7 }}>
              <div><strong style={{ color: '#000' }}>Model:</strong> {project.llm}</div>
              <div><strong style={{ color: '#000' }}>Context:</strong> {total} items</div>
              <div><strong style={{ color: '#000' }}>Messages:</strong> {messages.length}</div>
              <div><strong style={{ color: '#000' }}>Project:</strong> {project.owner}/{project.repo}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function ThinkingDots() {
  return (
    <span style={{ display: 'flex', gap: '4px' }}>
      {[0, 1, 2].map(i => (
        <span key={i} style={{
          width: '7px', height: '7px',
          background: '#000',
          borderRadius: '50%',
          animation: `pulse 1.2s ease-in-out ${i * 0.2}s infinite`,
        }} />
      ))}
      <style>{`
        @keyframes pulse {
          0%, 80%, 100% { opacity: 0.15; transform: scale(0.8); }
          40% { opacity: 1; transform: scale(1); }
        }
      `}</style>
    </span>
  )
}
