import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'
import type { Conversation, SourceFilter } from '@/types'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function generateId(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return Math.random().toString(36).slice(2) + Date.now().toString(36)
}

export function newConversation(sourceFilter: SourceFilter = 'all'): Conversation {
  const now = new Date()
  return {
    id: generateId(),
    title: 'New Conversation',
    messages: [],
    source_filter: sourceFilter,
    created_at: now,
    updated_at: now,
  }
}

export function formatTimestamp(date: Date): string {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export function formatRelativeTime(date: Date): string {
  const diff = Date.now() - date.getTime()
  const minutes = Math.floor(diff / 60000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  return date.toLocaleDateString()
}

export function truncate(str: string, maxLen: number): string {
  if (str.length <= maxLen) return str
  return str.slice(0, maxLen - 3) + '...'
}

export function sourceLabel(source: string): string {
  if (source === 'darglobal') return 'DarGlobal'
  if (source === 'wasalt') return 'Wasalt'
  return source
}

export function sourceColor(source: string): string {
  if (source === 'darglobal') return 'text-gold-400'
  if (source === 'wasalt') return 'text-blue-400'
  return 'text-gray-400'
}

export function sourceBadgeStyle(source: string): string {
  if (source === 'darglobal')
    return 'bg-gold-500/15 text-gold-400 border border-gold-500/30'
  if (source === 'wasalt')
    return 'bg-blue-500/15 text-blue-400 border border-blue-500/30'
  return 'bg-gray-500/15 text-gray-400 border border-gray-500/30'
}
