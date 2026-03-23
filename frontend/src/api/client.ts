import type {
  ExportResponse,
  GoPipelineMetrics,
  MirrorDashboardSnapshot,
  MirrorEventsResponse,
  MirrorInjectionsResponse,
  MirrorMetrics,
  TriggerInjectionResponse,
} from '../types/api'

const DEFAULT_AGENT_API = 'http://127.0.0.1:8001'
const DEFAULT_GO_API = 'http://127.0.0.1:8080'

const agentBase = (import.meta.env.VITE_AGENT_API_BASE_URL as string | undefined)?.trim() || DEFAULT_AGENT_API
const goBase = (import.meta.env.VITE_GO_API_BASE_URL as string | undefined)?.trim() || DEFAULT_GO_API

async function parseJson<T>(res: Response, endpoint: string): Promise<T> {
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`${endpoint} failed (${res.status}): ${body || res.statusText}`)
  }
  return (await res.json()) as T
}

async function getAgent<T>(path: string): Promise<T> {
  const res = await fetch(`${agentBase}${path}`, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  })
  return parseJson<T>(res, `GET ${path}`)
}

async function getGo<T>(path: string): Promise<T> {
  const res = await fetch(`${goBase}${path}`, {
    method: 'GET',
    headers: { Accept: 'application/json' },
  })
  return parseJson<T>(res, `GET ${path}`)
}

async function postAgent<T>(path: string, payload: Record<string, unknown> = {}): Promise<T> {
  const res = await fetch(`${agentBase}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json',
    },
    body: JSON.stringify(payload),
  })
  return parseJson<T>(res, `POST ${path}`)
}

export async function getMirrorMetrics(): Promise<MirrorMetrics> {
  return getAgent<MirrorMetrics>('/mirror/metrics')
}

export async function getMirrorDashboard(limit = 50): Promise<MirrorDashboardSnapshot> {
  return getAgent<MirrorDashboardSnapshot>(`/mirror/dashboard?limit=${encodeURIComponent(String(limit))}`)
}

export async function getGoPipelineMetrics(): Promise<GoPipelineMetrics> {
  return getGo<GoPipelineMetrics>('/api/v1/metrics/pipeline')
}

export async function getMirrorEvents(limit = 50): Promise<MirrorEventsResponse> {
  return getAgent<MirrorEventsResponse>(`/mirror/events?limit=${encodeURIComponent(String(limit))}`)
}

export async function getMirrorInjections(limit = 50): Promise<MirrorInjectionsResponse> {
  return getAgent<MirrorInjectionsResponse>(`/mirror/injections?limit=${encodeURIComponent(String(limit))}`)
}

export async function triggerInjection(attackType: string | null): Promise<TriggerInjectionResponse> {
  const payload = attackType ? { attack_type: attackType } : {}
  return postAgent<TriggerInjectionResponse>('/mirror/injections/trigger', payload)
}

export async function exportStix(): Promise<ExportResponse> {
  return postAgent<ExportResponse>('/mirror/exports/stix')
}

export async function exportReport(): Promise<ExportResponse> {
  return postAgent<ExportResponse>('/mirror/exports/report')
}

export function getConfiguredApiBases(): { agentApiBase: string; goApiBase: string } {
  return { agentApiBase: agentBase, goApiBase: goBase }
}
