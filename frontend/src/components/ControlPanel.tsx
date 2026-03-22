import { useState, type ReactElement } from 'react'

const ATTACK_PROFILES = [
  'AUTO',
  'REPUTATION_LAUNDERING',
  'GHOST_DOMAIN',
  'TTP_MISMATCH',
  'TIMESTAMP_MANIPULATION',
] as const

type AttackProfile = (typeof ATTACK_PROFILES)[number]

interface ControlPanelProps {
  onTriggerInjection: (attackType: string | null) => Promise<string>
  onExportStix: () => Promise<string>
  onExportReport: () => Promise<string>
  loading: boolean
}

export function ControlPanel({
  onTriggerInjection,
  onExportStix,
  onExportReport,
  loading,
}: ControlPanelProps): ReactElement {
  const [attackProfile, setAttackProfile] = useState<AttackProfile>('AUTO')
  const [status, setStatus] = useState<string>('')
  const [error, setError] = useState<string>('')

  const runAction = async (action: () => Promise<string>) => {
    setError('')
    try {
      const message = await action()
      setStatus(message)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Action failed.'
      setError(message)
    }
  }

  return (
    <section className="panel controls-panel" aria-label="Operator controls">
      <header className="panel-header">
        <h2>Operator Controls</h2>
      </header>

      <div className="control-group">
        <label htmlFor="attack-profile">Attack profile</label>
        <select
          id="attack-profile"
          value={attackProfile}
          disabled={loading}
          onChange={(event) => setAttackProfile(event.target.value as AttackProfile)}
        >
          {ATTACK_PROFILES.map((profile) => (
            <option key={profile} value={profile}>
              {profile}
            </option>
          ))}
        </select>
      </div>

      <div className="control-actions">
        <button
          type="button"
          disabled={loading}
          onClick={() =>
            void runAction(() =>
              onTriggerInjection(attackProfile === 'AUTO' ? null : attackProfile),
            )
          }
        >
          Launch Injection
        </button>
        <button type="button" disabled={loading} onClick={() => void runAction(onExportStix)}>
          Export STIX
        </button>
        <button type="button" disabled={loading} onClick={() => void runAction(onExportReport)}>
          Export Report
        </button>
      </div>

      {status ? <p className="action-status">{status}</p> : null}
      {error ? <p className="action-error">{error}</p> : null}
    </section>
  )
}
