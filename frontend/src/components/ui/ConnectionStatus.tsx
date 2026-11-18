'use client'

import { useEffect, useState } from 'react'
import { Wifi, WifiOff, Loader2 } from 'lucide-react'
import { api } from '@/lib/api'

type Status = 'checking' | 'online' | 'offline'

export default function ConnectionStatus() {
  const [status, setStatus] = useState<Status>('checking')

  useEffect(() => {
    const check = async () => {
      try {
        await api.health()
        setStatus('online')
      } catch {
        setStatus('offline')
      }
    }
    check()
    const interval = setInterval(check, 30000)
    return () => clearInterval(interval)
  }, [])

  if (status === 'checking') {
    return (
      <div className="flex items-center gap-1.5 text-xs text-slate-400">
        <Loader2 size={12} className="animate-spin" />
        <span>Connecting…</span>
      </div>
    )
  }

  if (status === 'offline') {
    return (
      <div className="flex items-center gap-1.5 text-xs text-red-400">
        <WifiOff size={12} />
        <span>Offline</span>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-1.5 text-xs text-emerald-400">
      <div className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
      <span>Connected</span>
    </div>
  )
}
