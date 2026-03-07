import { useEffect, useState } from 'react'
import RiskScore from './components/RiskScore'
import RiskExplanation from './components/RiskExplanation'
import RegionCards from './components/RegionCards'
import StressChart from './components/StressChart'
import IncidentFeed from './components/IncidentFeed'
import IncidentInput from './components/IncidentInput'
import SectorAlerts from './components/SectorAlerts'
import { analyzeIncident, healthCheck } from './api/backend'
import {
  regions,
  stressScoreHistory,
  riskFactors,
  incidents,
  sectorAlerts,
} from './data/sampleData'

const ODIN_URL =
  "https://openenergyhub.ornl.gov/api/explore/v2.1/catalog/datasets/odin-real-time-outages-county/records?select=state,county,name,metersaffected,reportedstarttime,estimatedrestorationtime,incident_cause,statuskind&where=state%20%3D%20'Texas'&limit=100"

const riskFromScore = (score) => {
  if (score >= 70) return 'high'
  if (score >= 40) return 'medium'
  return 'low'
}

const severityFromMeters = (meters) => {
  if (meters >= 20) return 'high'
  if (meters >= 5) return 'medium'
  return 'low'
}

const scoreFromMeters = (meters) => {
  if (meters <= 0) return 0
  return Math.min(100, Math.round(Math.log10(1 + meters) * 32))
}

const toIsoOrNow = (value) => {
  if (!value) return new Date().toISOString()
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? new Date().toISOString() : parsed.toISOString()
}

const toHourLabel = (iso) => {
  const d = new Date(iso)
  return `${String(d.getHours()).padStart(2, '0')}:00`
}

function App() {
  const [dashboard, setDashboard] = useState({
    score: 78,
    regions,
    stressScoreHistory,
    riskFactors,
    incidents,
    sectorAlerts,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [nlpLoading, setNlpLoading] = useState(false)
  const [nlpError, setNlpError] = useState('')
  const [backendConnected, setBackendConnected] = useState(false)

  useEffect(() => {
    healthCheck()
      .then(() => setBackendConnected(true))
      .catch(() => setBackendConnected(false))
  }, [])

  useEffect(() => {
    const loadLiveOutages = async () => {
      setLoading(true)
      setError('')

      try {
        const response = await fetch(ODIN_URL)
        if (!response.ok) {
          throw new Error(`ODIN request failed (${response.status})`)
        }

        const payload = await response.json()
        const raw = Array.isArray(payload.results) ? payload.results : []

        if (raw.length === 0) {
          throw new Error('ODIN returned no outage records')
        }

        const normalized = raw.map((r, index) => {
          const meters = Number(r.metersaffected) || 0
          const timestamp = toIsoOrNow(r.reportedstarttime || r.estimatedrestorationtime)
          const status = r.statuskind || 'Unknown'
          const cause = r.incident_cause || 'Unknown'
          const utility = r.name || 'Unknown Utility'
          const county = r.county || 'Unknown County'

          return {
            id: `${utility}-${county}-${index}`,
            meters,
            timestamp,
            status,
            cause,
            utility,
            county,
          }
        })

        normalized.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))

        const totalMeters = normalized.reduce((sum, x) => sum + x.meters, 0)
        const score = scoreFromMeters(totalMeters)

        const incidentsLive = normalized.slice(0, 20).map((x) => ({
          id: x.id,
          timestamp: x.timestamp,
          text: `${x.utility} outage in ${x.county} affecting ${x.meters} customers`,
          eventType: x.status,
          cause: x.cause,
          severity: severityFromMeters(x.meters),
          region: `${x.county}, TX`,
        }))

        const byCounty = normalized.reduce((acc, x) => {
          acc[x.county] = (acc[x.county] || 0) + x.meters
          return acc
        }, {})

        const regionsLive = Object.entries(byCounty)
          .sort((a, b) => b[1] - a[1])
          .slice(0, 4)
          .map(([county, meters], idx) => {
            const countyScore = scoreFromMeters(meters)
            return {
              id: `county-${idx}`,
              name: `${county} County`,
              abbreviation: 'TX',
              score: countyScore,
              risk: riskFromScore(countyScore),
            }
          })

        const byHour = normalized.reduce((acc, x) => {
          const hour = toHourLabel(x.timestamp)
          acc[hour] = (acc[hour] || 0) + x.meters
          return acc
        }, {})

        const stressLive = Object.entries(byHour)
          .sort((a, b) => a[0].localeCompare(b[0]))
          .slice(-12)
          .map(([time, meters]) => ({ time, score: scoreFromMeters(meters) }))

        const plannedCount = normalized.filter((x) => x.cause.toLowerCase().includes('planned')).length
        const pendingCount = normalized.filter((x) => x.status.toLowerCase().includes('pending')).length
        const highImpactCount = normalized.filter((x) => x.meters >= 20).length

        const totalSignals = Math.max(1, plannedCount + pendingCount + highImpactCount)
        const factorsLive = [
          {
            factor: 'Pending assessments',
            contribution: Math.round((pendingCount / totalSignals) * 100),
            severity: pendingCount > 8 ? 'high' : pendingCount > 3 ? 'medium' : 'low',
          },
          {
            factor: 'Planned outage activity',
            contribution: Math.round((plannedCount / totalSignals) * 100),
            severity: plannedCount > 6 ? 'medium' : 'low',
          },
          {
            factor: 'High-impact incidents (20+ customers)',
            contribution: Math.round((highImpactCount / totalSignals) * 100),
            severity: highImpactCount > 2 ? 'high' : highImpactCount > 0 ? 'medium' : 'low',
          },
        ]

        const topCounty = regionsLive[0]?.name || 'Texas'
        const topRisk = riskFromScore(score)
        const alertsLive = [
          {
            sector: 'Emergency Services',
            region: topCounty,
            recommendation: 'Prepare dispatch backup power coverage in top outage county.',
            priority: topRisk,
          },
          {
            sector: 'Hospitals',
            region: topCounty,
            recommendation: 'Confirm generator readiness and fuel levels for continuity.',
            priority: topRisk,
          },
          {
            sector: 'Transportation',
            region: topCounty,
            recommendation: 'Stage traffic signal contingency and field response teams.',
            priority: topRisk === 'high' ? 'high' : 'medium',
          },
        ]

        setDashboard({
          score,
          regions: regionsLive.length ? regionsLive : regions,
          stressScoreHistory: stressLive.length ? stressLive : stressScoreHistory,
          riskFactors: factorsLive,
          incidents: incidentsLive,
          sectorAlerts: alertsLive,
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load live outage data')
        setDashboard({
          score: 78,
          regions,
          stressScoreHistory,
          riskFactors,
          incidents,
          sectorAlerts,
        })
      } finally {
        setLoading(false)
      }
    }

    loadLiveOutages()
  }, [])

  const handleAnalyzeIncident = async (text) => {
    setNlpLoading(true)
    setNlpError('')
    try {
      const result = await analyzeIncident(text)
      const { incident, risk, alert } = result

      const newIncident = {
        id: `nlp-${Date.now()}`,
        timestamp: new Date().toISOString(),
        text,
        eventType: incident.event_type,
        cause: incident.cause,
        severity: incident.severity,
        region: incident.region,
      }

      setDashboard((prev) => {
        const score100 = Math.round(risk.risk_score * 100)
        const newScore = score100 > prev.score ? score100 : prev.score

        let newAlerts = prev.sectorAlerts
        if (alert.send_alert) {
          const priorityMap = { P1: 'high', P2: 'high', P3: 'medium', P4: 'low' }
          newAlerts = [
            {
              sector: alert.audience.replace(/_/g, ' '),
              region: incident.region,
              recommendation: alert.message,
              priority: priorityMap[alert.priority] || 'medium',
            },
            ...prev.sectorAlerts,
          ]
        }

        return {
          ...prev,
          score: newScore,
          incidents: [newIncident, ...prev.incidents],
          sectorAlerts: newAlerts,
        }
      })
    } catch (err) {
      console.error('NLP analysis failed:', err)
      setNlpError(err instanceof Error ? err.message : 'Analysis failed. Is the backend running?')
    } finally {
      setNlpLoading(false)
    }
  }

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
              <span
                className={`h-2 w-2 rounded-full ${
                  error ? 'bg-amber-500' : loading ? 'animate-pulse bg-cyan-400' : 'bg-emerald-500'
                }`}
              />
              <span className="text-sm text-slate-400">
                {error ? 'Live (fallback)' : loading ? 'Loading' : 'Live API'}
              </span>
              {backendConnected && (
                <span className="text-xs text-cyan-400">• NLP backend</span>
              )}
            </div>
          </div>
          {error ? (
            <p className="mt-2 text-xs text-amber-400">ODIN API unavailable: {error}</p>
          ) : null}
        </div>
      </header>

      {/* Main content */}
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* NLP incident input */}
        <div className="mb-6">
          <IncidentInput onAnalyze={handleAnalyzeIncident} loading={nlpLoading} />
          {nlpError && (
            <p className="mt-2 text-sm text-amber-400">
              {nlpError} — Start the backend with: <code className="rounded bg-slate-700 px-1">cd backend && uvicorn main:app --reload</code>
            </p>
          )}
        </div>

        {/* Top row: Risk score + Explanation */}
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-1">
            <RiskScore score={dashboard.score} />
          </div>
          <div className="lg:col-span-2">
            <RiskExplanation factors={dashboard.riskFactors} />
          </div>
        </div>

        {/* Region cards */}
        <div className="mt-6">
          <RegionCards regions={dashboard.regions} />
        </div>

        {/* Chart + Incident feed + Sector alerts */}
        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <StressChart data={dashboard.stressScoreHistory} />
          </div>
          <div>
            <IncidentFeed incidents={dashboard.incidents} />
          </div>
        </div>

        {/* Sector alerts - full width */}
        <div className="mt-6">
          <SectorAlerts alerts={dashboard.sectorAlerts} />
        </div>
      </main>
    </div>
  )
}

export default App
