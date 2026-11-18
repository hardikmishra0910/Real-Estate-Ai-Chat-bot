export type SourceFilter = 'all' | 'darglobal' | 'wasalt'

export interface SourceCitation {
  source: string
  title: string
  url: string
  excerpt: string
  relevance_score?: number
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: SourceCitation[]
  model_used?: string
  tokens_used?: number
  retrieved_chunks?: number
  timestamp: Date
  isLoading?: boolean
}

export interface Conversation {
  id: string
  title: string
  messages: ChatMessage[]
  source_filter: SourceFilter
  created_at: Date
  updated_at: Date
}

export interface ChatRequest {
  message: string
  conversation_id: string
  source_filter: SourceFilter
  conversation_history: Array<{ role: string; content: string }>
}

export interface ChatResponse {
  answer: string
  conversation_id: string
  sources: SourceCitation[]
  model_used: string
  tokens_used?: number
  retrieved_chunks: number
}

export interface HealthResponse {
  status: string
  version: string
  environment: string
  chromadb: string
  openrouter: string
  timestamp: string
}

export interface StatsResponse {
  total_documents: number
  total_chunks: number
  sources: Array<{
    source: string
    document_count: number
    chunk_count: number
    last_scraped: string | null
  }>
  chromadb_status: string
  embedding_model: string
}

export const SUGGESTED_QUESTIONS = [
  'What projects does DarGlobal offer?',
  'Tell me about DarGlobal\'s projects in Saudi Arabia.',
  'What property information is available on Wasalt?',
  'Compare the information available from DarGlobal and Wasalt.',
  'Which locations are represented in the collected data?',
  'Tell me about DarGlobal\'s luxury branded residences.',
  'What are typical property prices in Riyadh on Wasalt?',
  'What is the AIDA project by DarGlobal?',
]
