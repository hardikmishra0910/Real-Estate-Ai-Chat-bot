import { cn, sourceBadgeStyle, sourceLabel } from '@/lib/utils'

interface SourceBadgeProps {
  source: string
  className?: string
}

export default function SourceBadge({ source, className }: SourceBadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
        sourceBadgeStyle(source),
        className,
      )}
    >
      {sourceLabel(source)}
    </span>
  )
}
