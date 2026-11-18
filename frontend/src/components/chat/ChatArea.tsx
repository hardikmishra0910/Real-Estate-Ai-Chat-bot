'use client'

import { useEffect, useRef } from 'react'
import type { ChatMessage, SourceFilter } from '@/types'
import MessageBubble from './MessageBubble'
import WelcomeScreen from './WelcomeScreen'
import ChatInput from './ChatInput'

interface ChatAreaProps {
  messages: ChatMessage[]
  isLoading: boolean
  sourceFilter: SourceFilter
  onSend: (message: string) => void
}

export default function ChatArea({
  messages,
  isLoading,
  sourceFilter,
  onSend,
}: ChatAreaProps) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <WelcomeScreen onQuestion={onSend} />
        ) : (
          <div className="max-w-3xl mx-auto px-4 py-6 space-y-6">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <ChatInput
        onSend={onSend}
        isLoading={isLoading}
      />
    </div>
  )
}
