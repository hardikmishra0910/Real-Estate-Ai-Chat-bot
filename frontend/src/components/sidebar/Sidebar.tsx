'use client'

import { useState } from 'react'
import {
  Plus,
  MessageSquare,
  Clock,
  Filter,
  Lightbulb,
  Building2,
  MapPin,
  ChevronRight,
  X,
} from 'lucide-react'
import { cn, formatRelativeTime, truncate, sourceLabel } from '@/lib/utils'
import type { Conversation, SourceFilter } from '@/types'
import { SUGGESTED_QUESTIONS } from '@/types'

interface SidebarProps {
  conversations: Conversation[]
  activeId: string
  sourceFilter: SourceFilter
  onNewConversation: () => void
  onSelectConversation: (id: string) => void
  onSourceFilterChange: (f: SourceFilter) => void
  onSuggestedQuestion: (q: string) => void
  isOpen: boolean
  onClose: () => void
}

const SOURCE_FILTERS: { value: SourceFilter; label: string; color: string }[] = [
  { value: 'all', label: 'All Sources', color: 'bg-slate-500' },
  { value: 'darglobal', label: 'DarGlobal', color: 'bg-gold-500' },
  { value: 'wasalt', label: 'Wasalt', color: 'bg-blue-500' },
]

export default function Sidebar({
  conversations,
  activeId,
  sourceFilter,
  onNewConversation,
  onSelectConversation,
  onSourceFilterChange,
  onSuggestedQuestion,
  isOpen,
  onClose,
}: SidebarProps) {
  const [showAllSuggestions, setShowAllSuggestions] = useState(false)
  const displayedQuestions = showAllSuggestions
    ? SUGGESTED_QUESTIONS
    : SUGGESTED_QUESTIONS.slice(0, 4)

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-20 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={cn(
          'fixed lg:relative inset-y-0 left-0 z-30 lg:z-auto',
          'w-72 flex flex-col bg-navy-900 border-r border-white/5',
          'transition-transform duration-300',
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
        )}
      >
        {/* Header */}
        <div className="p-4 border-b border-white/5 flex items-center justify-between">
          <div>
            <h2 className="text-xs font-semibold text-gold-500 tracking-widest uppercase">
              Conversations
            </h2>
          </div>
          <button
            onClick={onClose}
            className="lg:hidden p-1 rounded hover:bg-white/5 text-slate-400"
          >
            <X size={16} />
          </button>
        </div>

        {/* New Conversation */}
        <div className="p-3 border-b border-white/5">
          <button
            onClick={onNewConversation}
            className="w-full flex items-center gap-2 px-3 py-2.5 rounded-lg
              bg-gold-500/10 hover:bg-gold-500/20 border border-gold-500/20
              hover:border-gold-500/40 text-gold-400 text-sm font-medium
              transition-all duration-200 group"
          >
            <Plus size={16} className="group-hover:rotate-90 transition-transform duration-200" />
            New Conversation
          </button>
        </div>

        {/* Source Filter */}
        <div className="p-3 border-b border-white/5">
          <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-1">
            <Filter size={9} />
            Source Filter
          </p>
          <div className="space-y-1">
            {SOURCE_FILTERS.map((f) => (
              <button
                key={f.value}
                onClick={() => onSourceFilterChange(f.value)}
                className={cn(
                  'w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-all',
                  sourceFilter === f.value
                    ? 'bg-white/8 text-white border border-white/10'
                    : 'text-slate-400 hover:bg-white/5 hover:text-white',
                )}
              >
                <div className={cn('w-2 h-2 rounded-full', f.color)} />
                {f.label}
                {sourceFilter === f.value && (
                  <ChevronRight size={12} className="ml-auto text-gold-500" />
                )}
              </button>
            ))}
          </div>
        </div>

        {/* Knowledge Indicators */}
        <div className="px-3 py-2 border-b border-white/5">
          <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-1">
            <Building2 size={9} />
            Knowledge Base
          </p>
          <div className="space-y-1.5">
            <div className="flex items-center gap-2 px-2 py-1.5 rounded bg-gold-500/5">
              <div className="w-1.5 h-1.5 rounded-full bg-gold-500" />
              <span className="text-xs text-gold-400">DarGlobal Projects</span>
            </div>
            <div className="flex items-center gap-2 px-2 py-1.5 rounded bg-blue-500/5">
              <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
              <span className="text-xs text-blue-400">Wasalt Properties</span>
            </div>
          </div>
        </div>

        {/* Suggested Questions */}
        <div className="p-3 border-b border-white/5 flex-1 overflow-y-auto">
          <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-1">
            <Lightbulb size={9} />
            Suggested Questions
          </p>
          <div className="space-y-1">
            {displayedQuestions.map((q, i) => (
              <button
                key={i}
                onClick={() => onSuggestedQuestion(q)}
                className="w-full text-left px-2.5 py-2 rounded-lg text-xs text-slate-400
                  hover:text-white hover:bg-white/5 transition-all duration-150
                  border border-transparent hover:border-white/5"
              >
                {q}
              </button>
            ))}
          </div>
          {!showAllSuggestions && SUGGESTED_QUESTIONS.length > 4 && (
            <button
              onClick={() => setShowAllSuggestions(true)}
              className="mt-2 text-xs text-gold-500/60 hover:text-gold-500 transition-colors"
            >
              Show more…
            </button>
          )}
        </div>

        {/* Conversation History */}
        {conversations.length > 0 && (
          <div className="p-3 overflow-y-auto max-h-48">
            <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest mb-2 flex items-center gap-1">
              <Clock size={9} />
              History
            </p>
            <div className="space-y-1">
              {conversations.map((conv) => (
                <button
                  key={conv.id}
                  onClick={() => onSelectConversation(conv.id)}
                  className={cn(
                    'w-full text-left px-2.5 py-2 rounded-lg text-xs transition-all',
                    activeId === conv.id
                      ? 'bg-white/8 text-white border border-white/8'
                      : 'text-slate-400 hover:bg-white/5 hover:text-white',
                  )}
                >
                  <div className="flex items-center gap-1.5">
                    <MessageSquare size={10} className="shrink-0 opacity-60" />
                    <span className="truncate">{conv.title}</span>
                  </div>
                  <div className="mt-0.5 text-[10px] text-slate-600 pl-4">
                    {formatRelativeTime(conv.updated_at)}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </aside>
    </>
  )
}
