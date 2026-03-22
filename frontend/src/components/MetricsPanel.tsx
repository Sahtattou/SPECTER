import type { ReactElement } from 'react'
import type { GoPipelineMetrics, MirrorMetrics } from '../types/api'

interface MetricsPanelProps {
  mirrorMetrics: MirrorMetrics | null
  goMetrics: GoPipelineMetrics | null
}

function metricValue(value: number | string | null | undefined): string {
  if (value === null || value === undefined) {
    return '—'
  }
  return typeof value === 'number' ? value.toLocaleString() : value
}

export function MetricsPanel({ mirrorMetrics, goMetrics }: MetricsPanelProps): ReactElement {
  const totalEvents = goMetrics?.total_events ?? 0
  const totalInjections = mirrorMetrics?.total_injections ?? 0
  const caughtInjections = mirrorMetrics?.caught_injections ?? 0
  const catchRate = mirrorMetrics?.catch_rate_percent ?? 0
  const realEvents = mirrorMetrics?.real_events ?? 0
  const freshnessSeconds = goMetrics?.freshness_age_seconds
  const freshness =
    typeof freshnessSeconds === 'number' && Number.isFinite(freshnessSeconds)
      ? `${freshnessSeconds}s`
      : 'n/a'

  return (
    <section className="panel metrics-panel" aria-label="Pipeline metrics">
      <header className="panel-header">
        <h2>Pipeline Overview</h2>
      </header>

      <div className="metric-grid metric-grid-4">
        <div className="metric-card">
          <span className="metric-label">Total Events</span>
          <strong className="metric-value">{metricValue(totalEvents)}</strong>
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
          <span className="metric-label">Real (BLUE)</span>
          <strong className="metric-value">{metricValue(realEvents)}</strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Freshness Age</span>
          <strong className="metric-value">{metricValue(freshness)}</strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Sources</span>
          <strong className="metric-value">{metricValue(goMetrics?.distinct_sources ?? 0)}</strong>
        </div>
      </div>
    </section>
  )
}
