import RiskScore from './components/RiskScore'
import RiskExplanation from './components/RiskExplanation'
import RegionCards from './components/RegionCards'
import StressChart from './components/StressChart'
import IncidentFeed from './components/IncidentFeed'
import SectorAlerts from './components/SectorAlerts'
import {
  regions,
  stressScoreHistory,
  riskFactors,
  incidents,
  sectorAlerts,
} from './data/sampleData'

function App() {
  return (
    <div className="min-h-screen bg-grid-dark text-slate-100">
      {/* Header */}
      <header className="border-b border-grid-border bg-grid-card/50 backdrop-blur">
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-cyan-500/20">
                <svg
                  className="h-6 w-6 text-cyan-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold tracking-tight">GridWatch</h1>
                <p className="text-xs text-slate-500">Outage Risk & Early Warning System</p>
              </div>
            </div>
            <div className="flex items-center gap-2 rounded-lg bg-slate-800/50 px-3 py-2">
              <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
              <span className="text-sm text-slate-400">Live</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Top row: Risk score + Explanation */}
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-1">
            <RiskScore score={78} />
          </div>
          <div className="lg:col-span-2">
            <RiskExplanation factors={riskFactors} />
          </div>
        </div>

        {/* Region cards */}
        <div className="mt-6">
          <RegionCards regions={regions} />
        </div>

        {/* Chart + Incident feed + Sector alerts */}
        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <StressChart data={stressScoreHistory} />
          </div>
          <div>
            <IncidentFeed incidents={incidents} />
          </div>
        </div>

        {/* Sector alerts - full width */}
        <div className="mt-6">
          <SectorAlerts alerts={sectorAlerts} />
        </div>
      </main>
    </div>
  )
}

export default App
