import type { ReactElement } from 'react'
import type { MirrorMetrics } from '../types/api'

interface MetricsPanelProps {
  mirrorMetrics: MirrorMetrics | null
  snapshotGeneratedAt: string | null
}

function metricValue(value: number | string | null | undefined): string {
  if (value === null || value === undefined) {
    return '—'
  }
  return typeof value === 'number' ? value.toLocaleString() : value
}

export function MetricsPanel({ mirrorMetrics, snapshotGeneratedAt }: MetricsPanelProps): ReactElement {
  const totalEvents = mirrorMetrics?.total_events ?? 0
  const mirrorTotalEvents = mirrorMetrics?.mirror_total_events
  const pipelineRunTotal = mirrorMetrics?.pipeline_run_total
  const validatedEvents = mirrorMetrics?.validated_events ?? 0
  const quarantinedEvents = mirrorMetrics?.quarantined_events ?? 0
  const totalInjections = mirrorMetrics?.total_injections ?? 0
  const caughtInjections = mirrorMetrics?.caught_injections ?? 0
  const catchRate = mirrorMetrics?.catch_rate_percent ?? 0
  const freshnessSeconds = mirrorMetrics?.freshness_age_seconds
  const freshness =
    typeof freshnessSeconds === 'number' && Number.isFinite(freshnessSeconds)
      ? `${freshnessSeconds}s`
      : 'n/a'
  const sources = mirrorMetrics?.distinct_sources ?? 0
  const snapshotLabel = snapshotGeneratedAt ? new Date(snapshotGeneratedAt).toLocaleTimeString() : 'n/a'

  return (
    <section className="panel metrics-panel" aria-label="Pipeline metrics">
      <header className="panel-header">
        <h2>Pipeline Overview</h2>
      </header>

      <div className="metric-grid metric-grid-4">
        <div className="metric-card">
          <span className="metric-label">Total Events</span>
          <strong className="metric-value">{metricValue(totalEvents)}</strong>
          <small className="metric-subvalue">
            unique {metricValue(mirrorTotalEvents)} · runs {metricValue(pipelineRunTotal)}
          </small>
        </div>
        <div className="metric-card">
          <span className="metric-label">Injections</span>
          <strong className="metric-value">{metricValue(totalInjections)}</strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Caught</span>
          <strong className="metric-value">{metricValue(caughtInjections)}</strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Catch Rate</span>
          <strong className="metric-value">{metricValue(`${catchRate.toFixed(1)}%`)}</strong>
        </div>
      </div>

      <div className="metric-grid metric-grid-3">
        <div className="metric-card">
          <span className="metric-label">Validated</span>
          <strong className="metric-value">{metricValue(validatedEvents)}</strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Quarantined</span>
          <strong className="metric-value">{metricValue(quarantinedEvents)}</strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Freshness Age</span>
          <strong className="metric-value">{metricValue(freshness)}</strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Sources</span>
          <strong className="metric-value">{metricValue(sources)}</strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Snapshot</span>
          <strong className="metric-value">{metricValue(snapshotLabel)}</strong>
        </div>
      </div>
    </section>
  )
}
