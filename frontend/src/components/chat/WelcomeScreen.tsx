'use client'

import { Sparkles, Building2, MapPin, TrendingUp, Search } from 'lucide-react'
import { SUGGESTED_QUESTIONS } from '@/types'
import Logo from '@/components/ui/Logo'

interface WelcomeScreenProps {
  onQuestion: (q: string) => void
}

const FEATURE_CARDS = [
  {
    icon: Building2,
    title: 'DarGlobal Projects',
    desc: 'Explore luxury developments across UAE, Saudi Arabia, Oman, Qatar, Spain & UK.',
    color: 'text-gold-400',
    bg: 'bg-gold-500/5 border-gold-500/20',
  },
  {
    icon: MapPin,
    title: 'Wasalt Listings',
    desc: 'Browse Saudi Arabian property listings for sale and rent across major cities.',
    color: 'text-blue-400',
    bg: 'bg-blue-500/5 border-blue-500/20',
  },
  {
    icon: Search,
    title: 'Semantic Search',
    desc: 'Ask in plain English — the system finds the most relevant property data for you.',
    color: 'text-purple-400',
    bg: 'bg-purple-500/5 border-purple-500/20',
  },
  {
    icon: TrendingUp,
    title: 'Investment Insights',
    desc: 'Get information on property types, amenities, and locations from verified sources.',
    color: 'text-emerald-400',
    bg: 'bg-emerald-500/5 border-emerald-500/20',
  },
]

export default function WelcomeScreen({ onQuestion }: WelcomeScreenProps) {
  return (
    <div className="flex flex-col items-center justify-center h-full px-6 py-8 text-center max-w-3xl mx-auto">
      {/* Logo + hero */}
      <div className="mb-8">
        <div className="flex justify-center mb-4">
          <Logo size="lg" showTagline />
        </div>
        <p className="text-slate-400 text-sm max-w-md leading-relaxed">
          Your AI-powered guide to DarGlobal luxury projects and Wasalt Saudi
          Arabian property listings. Ask anything — answers are grounded in
          collected public data.
        </p>
      </div>

      {/* Feature cards */}
      <div className="grid grid-cols-2 gap-3 w-full mb-8">
        {FEATURE_CARDS.map((card, i) => (
          <div
            key={i}
            className={`luxury-card rounded-xl p-4 text-left border ${card.bg}`}
          >
            <card.icon size={18} className={`${card.color} mb-2`} />
            <h3 className="text-sm font-semibold text-white mb-1">{card.title}</h3>
            <p className="text-xs text-slate-500 leading-relaxed">{card.desc}</p>
          </div>
        ))}
      </div>

      {/* Suggested questions */}
      <div className="w-full">
        <p className="text-xs text-slate-500 uppercase tracking-widest mb-3 flex items-center justify-center gap-1">
          <Sparkles size={10} />
          Try asking
        </p>
        <div className="grid grid-cols-1 gap-2">
          {SUGGESTED_QUESTIONS.slice(0, 4).map((q, i) => (
            <button
              key={i}
              onClick={() => onQuestion(q)}
              className="text-left px-4 py-3 rounded-xl bg-navy-800/60 border border-white/5
                hover:border-gold-500/30 hover:bg-navy-700/60 text-sm text-slate-300
                hover:text-white transition-all duration-200 group"
            >
              <span className="text-gold-500/40 group-hover:text-gold-500/60 mr-2">›</span>
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Disclaimer */}
      <p className="mt-6 text-[10px] text-slate-700 max-w-sm leading-relaxed">
        EstateIQ answers only from collected public data. Prices and details may
        have changed since collection. Always verify with the original source.
      </p>
    </div>
  )
}
