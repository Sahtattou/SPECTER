import { useCallback, useEffect, useMemo, useState } from 'react'

import {
  exportReport,
  exportStix,
  getConfiguredApiBases,
  getMirrorDashboard,
  triggerInjection,
} from '../api/client'
import type {
  MirrorEvent,
  MirrorMetrics,
  InjectionActivity,
} from '../types/api'

const DEFAULT_REFRESH_SECONDS = 10

export interface DashboardDataState {
  mirrorMetrics: MirrorMetrics | null
  snapshotGeneratedAt: string | null
  events: MirrorEvent[]
  injections: InjectionActivity[]
  loading: boolean
  error: string | null
  refresh: () => Promise<void>
  triggerManualInjection: (attackType: string | null) => Promise<string>
  runStixExport: () => Promise<string>
  runReportExport: () => Promise<string>
  apiBases: { agentApiBase: string; goApiBase: string }
}

export function useDashboardData(autoRefreshSeconds = DEFAULT_REFRESH_SECONDS): DashboardDataState {
  const [mirrorMetrics, setMirrorMetrics] = useState<MirrorMetrics | null>(null)
  const [snapshotGeneratedAt, setSnapshotGeneratedAt] = useState<string | null>(null)
  const [events, setEvents] = useState<MirrorEvent[]>([])
  const [injections, setInjections] = useState<InjectionActivity[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const snapshot = await getMirrorDashboard(50)
      setMirrorMetrics(snapshot.metrics)
      setEvents(snapshot.events)
      setInjections(snapshot.injections)
      setSnapshotGeneratedAt(snapshot.snapshot_generated_at)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load dashboard data.'
      setError(message)
    } finally {
      setLoading(false)
    }
  }, [])

  const triggerManualInjection = useCallback(async (attackType: string | null) => {
    const response = await triggerInjection(attackType)
    await refresh()
    return `Injected ${response.attack_type} · ${response.raw_value}`
  }, [refresh])

  const runStixExport = useCallback(async () => {
    const response = await exportStix()
    await refresh()
    return response.artifact_path
  }, [refresh])

  const runReportExport = useCallback(async () => {
    const response = await exportReport()
    await refresh()
    return response.artifact_path
  }, [refresh])

  useEffect(() => {
    void refresh()
  }, [refresh])

  useEffect(() => {
    if (autoRefreshSeconds <= 0) {
      return undefined
    }
    const timer = window.setInterval(() => {
      void refresh()
    }, autoRefreshSeconds * 1000)
    return () => {
      window.clearInterval(timer)
    }
  }, [autoRefreshSeconds, refresh])

  const apiBases = useMemo(() => getConfiguredApiBases(), [])

  return {
    mirrorMetrics,
    snapshotGeneratedAt,
    events,
    injections,
    loading,
    error,
    refresh,
    triggerManualInjection,
    runStixExport,
    runReportExport,
    apiBases,
  }
}
