import { ControlPanel } from './components/ControlPanel'
import { EventsTable } from './components/EventsTable'
import { InjectionsPanel } from './components/InjectionsPanel'
import { MetricsPanel } from './components/MetricsPanel'
import { useDashboardData } from './hooks/useDashboardData'
import './App.css'

function App() {
  const {
    mirrorMetrics,
    goMetrics,
    events,
    injections,
    loading,
    error,
    triggerManualInjection,
    runStixExport,
    runReportExport,
    apiBases,
  } = useDashboardData(10)

  return (
    <main className="app-shell">
      <header className="app-header">
        <p className="signal-banner">Threat grid uplink active · detector online · stream synchronized</p>
        <h1>SPECTER Cyber Operations Console</h1>
        <p className="subtitle">
          Tauri desktop command surface for live telemetry, controlled red injections, and export workflows.
        </p>
        <div className="endpoint-strip">
          <span>Agents API: {apiBases.agentApiBase}</span>
          <span>Go API: {apiBases.goApiBase}</span>
        </div>
      </header>

      {error ? <p className="error-banner">{error}</p> : null}

      <section className="grid-top">
        <ControlPanel
          onTriggerInjection={triggerManualInjection}
          onExportStix={runStixExport}
          onExportReport={runReportExport}
          loading={loading}
        />
        <MetricsPanel mirrorMetrics={mirrorMetrics} goMetrics={goMetrics} />
      </section>

      <section className="grid-bottom">
        <EventsTable events={events} />
        <InjectionsPanel injections={injections} />
      </section>
    </main>
  )
}

export default App
