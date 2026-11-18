'use client'

import { Bot, User, Copy, Check } from 'lucide-react'
import { useState } from 'react'
import { cn, formatTimestamp } from '@/lib/utils'
import type { ChatMessage } from '@/types'
import SourcePanel from './SourcePanel'

interface MessageBubbleProps {
  message: ChatMessage
}

function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-1 py-2">
      <div className="typing-dot" />
      <div className="typing-dot" />
      <div className="typing-dot" />
    </div>
  )
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const [copied, setCopied] = useState(false)
  const isUser = message.role === 'user'

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div
      className={cn(
        'flex gap-3 animate-slide-up group',
        isUser ? 'flex-row-reverse' : 'flex-row',
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          'shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-0.5',
          isUser
            ? 'bg-navy-700 border border-gold-500/30'
            : 'bg-gradient-to-br from-gold-500 to-gold-700',
        )}
      >
        {isUser ? (
          <User size={14} className="text-gold-400" />
        ) : (
          <Bot size={14} className="text-navy-950" />
        )}
      </div>

      {/* Bubble */}
      <div className={cn('max-w-[80%] flex flex-col', isUser ? 'items-end' : 'items-start')}>
        <div
          className={cn(
            'relative rounded-2xl px-4 py-3 text-sm leading-relaxed',
            isUser
              ? 'msg-user rounded-tr-sm text-slate-100'
              : 'msg-assistant rounded-tl-sm text-slate-200',
          )}
        >
          {message.isLoading ? (
            <TypingIndicator />
          ) : (
            <div className="whitespace-pre-wrap break-words">{message.content}</div>
          )}

          {/* Copy button */}
          {!message.isLoading && !isUser && (
            <button
              onClick={handleCopy}
              className="absolute -top-2 -right-2 opacity-0 group-hover:opacity-100
                p-1 rounded-full bg-navy-800 border border-white/10
                text-slate-500 hover:text-gold-400 transition-all"
              title="Copy response"
            >
              {copied ? <Check size={11} /> : <Copy size={11} />}
            </button>
          )}
        </div>

        {/* Sources */}
        {!isUser && !message.isLoading && message.sources && message.sources.length > 0 && (
          <div className="w-full mt-1">
            <SourcePanel sources={message.sources} />
          </div>
        )}

        {/* Meta row */}
        <div className="flex items-center gap-2 mt-1 px-1">
          <span className="text-[10px] text-slate-600">
            {formatTimestamp(message.timestamp)}
          </span>
          {!isUser && message.model_used && !message.isLoading && (
            <span className="text-[10px] text-slate-700">· {message.model_used}</span>
          )}
        </div>
      </div>
    </div>
  )
}
