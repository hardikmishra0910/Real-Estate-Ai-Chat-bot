'use client'

import { ExternalLink, FileText, Globe, ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'
import { cn, sourceLabel, sourceBadgeStyle, truncate } from '@/lib/utils'
import type { SourceCitation } from '@/types'

interface SourcePanelProps {
  sources: SourceCitation[]
}

export default function SourcePanel({ sources }: SourcePanelProps) {
  const [expanded, setExpanded] = useState<number | null>(null)

  if (!sources || sources.length === 0) return null

  return (
    <div className="mt-3 space-y-2">
      <p className="text-[10px] font-semibold text-slate-500 uppercase tracking-widest flex items-center gap-1">
        <FileText size={9} />
        Sources ({sources.length})
      </p>

      <div className="space-y-1.5">
        {sources.map((src, i) => (
          <div
            key={i}
            className="rounded-lg border border-white/5 bg-navy-800/50 overflow-hidden"
          >
            {/* Header row */}
            <div
              className="flex items-start gap-2 p-2.5 cursor-pointer hover:bg-white/3 transition-colors"
              onClick={() => setExpanded(expanded === i ? null : i)}
            >
              <Globe size={12} className="mt-0.5 text-slate-500 shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span
                    className={cn(
                      'text-[10px] px-1.5 py-0.5 rounded font-medium',
                      sourceBadgeStyle(src.source),
                    )}
                  >
                    {sourceLabel(src.source)}
                  </span>
                  {src.relevance_score !== undefined && (
                    <span className="text-[9px] text-slate-600">
                      {Math.round(src.relevance_score * 100)}% match
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-300 mt-0.5 leading-tight">
                  {truncate(src.title, 70)}
                </p>
              </div>
              <div className="flex items-center gap-1 shrink-0">
                <a
                  href={src.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="p-1 rounded hover:bg-white/10 text-slate-500 hover:text-gold-400 transition-colors"
                  title="Open source URL"
                >
                  <ExternalLink size={11} />
                </a>
                {expanded === i ? (
                  <ChevronUp size={11} className="text-slate-500" />
                ) : (
                  <ChevronDown size={11} className="text-slate-500" />
                )}
              </div>
            </div>

            {/* Excerpt */}
            {expanded === i && (
              <div className="px-2.5 pb-2.5 pt-0 border-t border-white/5">
                <p className="text-[11px] text-slate-400 leading-relaxed mt-2">
                  {src.excerpt}
                </p>
                <a
                  href={src.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="mt-1.5 inline-flex items-center gap-1 text-[10px] text-gold-500/70
                    hover:text-gold-400 transition-colors"
                >
                  <ExternalLink size={9} />
                  {truncate(src.url, 60)}
                </a>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
