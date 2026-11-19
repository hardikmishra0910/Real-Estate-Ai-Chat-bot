import type {
  ChatRequest,
  ChatResponse,
  HealthResponse,
  StatsResponse,
} from '@/types'

// In production on Render, calls go to /api/* which Next.js rewrites to the backend.
// NEXT_PUBLIC_API_URL is baked in at build time via next.config.js env block.
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function apiFetch<T>(
  path: string,
  options?: RequestInit,
  timeoutMs = 60000,
): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)

  // Always call the backend directly using the baked-in URL
  const url = `${API_URL}${path}`

  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers ?? {}),
      },
    })
    clearTimeout(timer)

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }))
      throw new Error(err.detail ?? `HTTP ${res.status}`)
    }

    return res.json() as Promise<T>
  } catch (err: unknown) {
    clearTimeout(timer)
    if (err instanceof Error && err.name === 'AbortError') {
      throw new Error('Request timed out. The server may be starting — please try again in 30 seconds.')
    }
    throw err
  }
}

export const api = {
  health: () => apiFetch<HealthResponse>('/health'),
  stats:  () => apiFetch<StatsResponse>('/api/stats'),
  chat:   (payload: ChatRequest) =>
    apiFetch<ChatResponse>('/api/chat', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
  scrape: (sources: string[] = ['darglobal', 'wasalt'], forceRefresh = false) =>
    apiFetch('/api/scrape', {
      method: 'POST',
      body: JSON.stringify({ sources, force_refresh: forceRefresh }),
    }),
}
