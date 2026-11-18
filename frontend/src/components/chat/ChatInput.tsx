'use client'

import { useState, useRef, KeyboardEvent } from 'react'
import { Send, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ChatInputProps {
  onSend: (message: string) => void
  isLoading: boolean
  disabled?: boolean
  placeholder?: string
}

export default function ChatInput({
  onSend,
  isLoading,
  disabled,
  placeholder = 'Ask about DarGlobal projects or Wasalt properties…',
}: ChatInputProps) {
  const [input, setInput] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const canSend = input.trim().length > 0 && !isLoading && !disabled

  const handleSend = () => {
    if (!canSend) return
    const msg = input.trim()
    setInput('')
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
    }
    onSend(msg)
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleInput = () => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }

  return (
    <div className="p-4 border-t border-white/5 bg-navy-950/80 backdrop-blur-sm">
      <div className="max-w-3xl mx-auto">
        <div
          className={cn(
            'flex items-end gap-3 rounded-2xl border px-4 py-3 transition-all duration-200',
            'bg-navy-800/60 backdrop-blur-sm',
            isLoading || disabled
              ? 'border-white/5'
              : 'border-white/10 hover:border-gold-500/30 focus-within:border-gold-500/40',
          )}
        >
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            onInput={handleInput}
            disabled={isLoading || disabled}
            placeholder={placeholder}
            rows={1}
            className={cn(
              'flex-1 bg-transparent text-sm text-slate-200 placeholder:text-slate-600',
              'resize-none outline-none leading-relaxed',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'max-h-40 min-h-[24px]',
            )}
          />

          <button
            onClick={handleSend}
            disabled={!canSend}
            className={cn(
              'shrink-0 w-9 h-9 rounded-xl flex items-center justify-center',
              'transition-all duration-200',
              canSend
                ? 'bg-gradient-to-br from-gold-500 to-gold-700 hover:from-gold-400 hover:to-gold-600 text-navy-950 shadow-lg shadow-gold-500/20'
                : 'bg-white/5 text-slate-600 cursor-not-allowed',
            )}
            title="Send message"
          >
            {isLoading ? (
              <Loader2 size={16} className="animate-spin" />
            ) : (
              <Send size={15} />
            )}
          </button>
        </div>

        <p className="text-center text-[10px] text-slate-700 mt-2">
          Answers grounded in collected DarGlobal & Wasalt data · Press Enter to send
        </p>
      </div>
    </div>
  )
}
