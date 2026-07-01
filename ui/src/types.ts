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
  status: 'INDEXED' | 'PENDING' | 'FAILED' | 'SYNCING'
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
