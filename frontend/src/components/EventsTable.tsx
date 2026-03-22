import type { ReactElement } from 'react'
import type { MirrorEvent } from '../types/api'
import { formatUtc } from '../utils/time'

interface EventsTableProps {
  events: MirrorEvent[]
}

function verdictFor(event: MirrorEvent): string {
  const stage = event.pipeline_stage ?? ''
  if (stage === 'quarantined' && event.poison_detected === true) {
    return 'Detected'
  }
  if ((stage === 'validated' || stage === 'scored') && event.poison_detected === false) {
    return 'Passed'
  }
  if (event.is_synthetic && event.poison_detected === false) {
    return 'Missed'
  }
  return 'Review'
}

export function EventsTable({ events }: EventsTableProps): ReactElement {
  return (
    <section className="panel events-panel" aria-label="Live IOC feed">
      <header className="panel-header">
        <h2>Live IOC Feed</h2>
      </header>

      {events.length === 0 ? (
        <p className="empty-state">No events yet. Trigger an injection or ingest data.</p>
      ) : (
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>Collected</th>
                <th>Origin</th>
                <th>Type</th>
                <th>IOC</th>
                <th>Verdict</th>
                <th>Score</th>
              </tr>
            </thead>
            <tbody>
              {events.map((event) => (
                <tr key={event.ioc_uuid}>
                  <td>{formatUtc(event.collected_at)}</td>
                  <td>{event.is_synthetic ? 'Injected simulation' : 'Real telemetry'}</td>
                  <td>{event.ioc_type}</td>
                  <td className="mono">{event.raw_value}</td>
                  <td>{verdictFor(event)}</td>
                  <td>{event.composite_score?.toFixed(1) ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
