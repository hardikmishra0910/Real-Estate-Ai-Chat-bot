import { Building2 } from 'lucide-react'

interface LogoProps {
  size?: 'sm' | 'md' | 'lg'
  showTagline?: boolean
}

export default function Logo({ size = 'md', showTagline = false }: LogoProps) {
  const iconSizes = { sm: 18, md: 24, lg: 32 }
  const textSizes = { sm: 'text-lg', md: 'text-xl', lg: 'text-3xl' }
  const iqSizes = { sm: 'text-xs', md: 'text-sm', lg: 'text-base' }

  return (
    <div className="flex items-center gap-2">
      <div className="relative">
        <div className="absolute inset-0 bg-gold-500/20 rounded-lg blur-sm" />
        <div className="relative bg-gradient-to-br from-gold-500 to-gold-700 rounded-lg p-1.5">
          <Building2 size={iconSizes[size]} className="text-navy-950" />
        </div>
      </div>
      <div>
        <div className="flex items-baseline gap-0.5">
          <span className={`font-bold tracking-tight text-white ${textSizes[size]}`}>
            Estate
          </span>
          <span className={`font-bold tracking-tight gradient-text ${textSizes[size]}`}>
            IQ
          </span>
          {size !== 'sm' && (
            <span className={`ml-1 font-light text-gold-500/60 ${iqSizes[size]}`}>™</span>
          )}
        </div>
        {showTagline && (
          <p className="text-xs text-slate-400 tracking-widest uppercase font-light">
            Real Estate Intelligence
          </p>
        )}
      </div>
    </div>
  )
}
