'use client'

import { useState, useCallback } from 'react'
import { Menu, Database, RefreshCw } from 'lucide-react'
import Logo from '@/components/ui/Logo'
import ConnectionStatus from '@/components/ui/ConnectionStatus'
import Sidebar from '@/components/sidebar/Sidebar'
import ChatArea from '@/components/chat/ChatArea'
import { api } from '@/lib/api'
import { generateId, newConversation } from '@/lib/utils'
import type { ChatMessage, Conversation, SourceFilter } from '@/types'

export default function HomePage() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [activeConvId, setActiveConvId] = useState<string>('')
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>('all')
  const [isLoading, setIsLoading] = useState(false)
  const [isScraping, setIsScraping] = useState(false)
  const [scrapeMsg, setScrapeMsg] = useState('')

  // Active conversation
  const activeConv = conversations.find((c) => c.id === activeConvId)

  const handleNewConversation = useCallback(() => {
    const conv = newConversation(sourceFilter)
    setConversations((prev) => [conv, ...prev])
    setActiveConvId(conv.id)
    setSidebarOpen(false)
  }, [sourceFilter])

  const ensureConversation = useCallback((): string => {
    if (activeConvId && conversations.some((c) => c.id === activeConvId)) {
      return activeConvId
    }
    const conv = newConversation(sourceFilter)
    setConversations((prev) => [conv, ...prev])
    setActiveConvId(conv.id)
    return conv.id
  }, [activeConvId, conversations, sourceFilter])

  const handleSend = useCallback(
    async (message: string) => {
      if (!message.trim() || isLoading) return

      const convId = ensureConversation()

      const userMsg: ChatMessage = {
        id: generateId(),
        role: 'user',
        content: message,
        timestamp: new Date(),
      }

      const loadingMsg: ChatMessage = {
        id: generateId(),
        role: 'assistant',
        content: '',
        timestamp: new Date(),
        isLoading: true,
      }

      // Add user message + loading indicator
      setConversations((prev) =>
        prev.map((c) => {
          if (c.id !== convId) return c
          const updated = {
            ...c,
            messages: [...c.messages, userMsg, loadingMsg],
            updated_at: new Date(),
            title:
              c.messages.length === 0
                ? message.slice(0, 50)
                : c.title,
          }
          return updated
        }),
      )
      setIsLoading(true)

      // Build history for context
      const currentConv = conversations.find((c) => c.id === convId)
      const history = (currentConv?.messages ?? [])
        .filter((m) => !m.isLoading)
        .slice(-10)
        .map((m) => ({ role: m.role, content: m.content }))

      try {
        const response = await api.chat({
          message,
          conversation_id: convId,
          source_filter: sourceFilter,
          conversation_history: history,
        })

        const assistantMsg: ChatMessage = {
          id: generateId(),
          role: 'assistant',
          content: response.answer,
          sources: response.sources,
          model_used: response.model_used,
          tokens_used: response.tokens_used,
          retrieved_chunks: response.retrieved_chunks,
          timestamp: new Date(),
        }

        setConversations((prev) =>
          prev.map((c) => {
            if (c.id !== convId) return c
            return {
              ...c,
              messages: [
                ...c.messages.filter((m) => !m.isLoading),
                assistantMsg,
              ],
              updated_at: new Date(),
            }
          }),
        )
      } catch (err: unknown) {
        const errorMsg: ChatMessage = {
          id: generateId(),
          role: 'assistant',
          content:
            err instanceof Error
              ? `⚠️ ${err.message}`
              : '⚠️ An unexpected error occurred. Please try again.',
          timestamp: new Date(),
        }
        setConversations((prev) =>
          prev.map((c) => {
            if (c.id !== convId) return c
            return {
              ...c,
              messages: [
                ...c.messages.filter((m) => !m.isLoading),
                errorMsg,
              ],
            }
          }),
        )
      } finally {
        setIsLoading(false)
      }
    },
    [isLoading, ensureConversation, conversations, sourceFilter],
  )

  const handleScrape = async () => {
    setIsScraping(true)
    setScrapeMsg('Scraping started…')
    try {
      const res = await api.scrape(['darglobal', 'wasalt'], false) as { message?: string }
      setScrapeMsg(res?.message ?? 'Scraping started in background.')
    } catch (e: unknown) {
      setScrapeMsg(e instanceof Error ? e.message : 'Scrape request failed.')
    } finally {
      setIsScraping(false)
      setTimeout(() => setScrapeMsg(''), 5000)
    }
  }

  const currentMessages = activeConv?.messages ?? []

  return (
    <div className="flex h-screen bg-navy-950 overflow-hidden">
      {/* Sidebar */}
      <Sidebar
        conversations={conversations}
        activeId={activeConvId}
        sourceFilter={sourceFilter}
        onNewConversation={handleNewConversation}
        onSelectConversation={(id) => {
          setActiveConvId(id)
          setSidebarOpen(false)
        }}
        onSourceFilterChange={setSourceFilter}
        onSuggestedQuestion={(q) => {
          setSidebarOpen(false)
          handleSend(q)
        }}
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      {/* Main content */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header */}
        <header className="flex items-center justify-between px-4 py-3 border-b border-white/5 bg-navy-900/80 backdrop-blur-sm shrink-0">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden p-2 rounded-lg hover:bg-white/5 text-slate-400"
            >
              <Menu size={18} />
            </button>
            <Logo size="sm" />
          </div>

          {/* Knowledge pill */}
          <div className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-navy-800/60 border border-white/5">
            <div className="w-1.5 h-1.5 rounded-full bg-gold-500" />
            <span className="text-[10px] text-slate-400 font-medium">DarGlobal</span>
            <span className="text-slate-700">·</span>
            <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
            <span className="text-[10px] text-slate-400 font-medium">Wasalt</span>
          </div>

          <div className="flex items-center gap-3">
            {/* Scrape button */}
            <button
              onClick={handleScrape}
              disabled={isScraping}
              className="hidden sm:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg
                text-[10px] text-slate-500 hover:text-slate-300 hover:bg-white/5
                border border-transparent hover:border-white/5 transition-all"
              title="Re-scrape data sources"
            >
              <RefreshCw size={11} className={isScraping ? 'animate-spin' : ''} />
              {isScraping ? 'Scraping…' : 'Refresh Data'}
            </button>

            <ConnectionStatus />
          </div>
        </header>

        {/* Scrape status banner */}
        {scrapeMsg && (
          <div className="px-4 py-2 bg-gold-500/10 border-b border-gold-500/20 text-xs text-gold-400 text-center">
            {scrapeMsg}
          </div>
        )}

        {/* Chat area */}
        <ChatArea
          messages={currentMessages}
          isLoading={isLoading}
          sourceFilter={sourceFilter}
          onSend={handleSend}
        />
      </div>
    </div>
  )
}
