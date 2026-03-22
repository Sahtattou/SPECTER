import type { ReactElement } from 'react'
import type { InjectionActivity } from '../types/api'
import { formatUtc, statusLabel } from '../utils/time'

interface InjectionsPanelProps {
  injections: InjectionActivity[]
}

export function InjectionsPanel({ injections }: InjectionsPanelProps): ReactElement {
  return (
    <section className="panel injections-panel" aria-label="Red activity">
      <header className="panel-header">
        <h2>Red Agent Activity</h2>
      </header>

      {injections.length === 0 ? (
        <p className="empty-state">No injections logged yet.</p>
      ) : (
        <ul className="injection-list">
          {injections.map((entry) => {
            const status = statusLabel(entry.detected)
            return (
              <li key={entry.injection_id} className="injection-item">
                <div className="injection-head">
                  <strong>{entry.attack_type}</strong>
                  <span className={`status status-${status.toLowerCase()}`}>{status}</span>
                </div>
                <p className="mono">{entry.raw_value}</p>
                <p className="muted">{formatUtc(entry.injected_at)}</p>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}
