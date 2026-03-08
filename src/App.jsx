import { useEffect, useState } from 'react'
import RiskScore from './components/RiskScore'
import RiskExplanation from './components/RiskExplanation'
import RegionCards from './components/RegionCards'
import StressChart from './components/StressChart'
import IncidentFeed from './components/IncidentFeed'
import IncidentInput from './components/IncidentInput'
import NaturalDisasterFeed from './components/NaturalDisasterFeed'
import SectorAlerts from './components/SectorAlerts'
import { analyzeIncident, healthCheck, refreshDataset, fetchDisasterEvents, suggestResponse } from './api/backend'
import {
  regions,
  stressScoreHistory,
  riskFactors,
  incidents,
  sectorAlerts,
} from './data/sampleData'

const ODIN_URL =
  "https://openenergyhub.ornl.gov/api/explore/v2.1/catalog/datasets/odin-real-time-outages-county/records?select=state,county,name,metersaffected,reportedstarttime,estimatedrestorationtime,incident_cause,statuskind&limit=100"

const STATE_ABBREVIATIONS = {
  Alabama: 'AL',
  Alaska: 'AK',
  Arizona: 'AZ',
  Arkansas: 'AR',
  California: 'CA',
  Colorado: 'CO',
  Connecticut: 'CT',
  Delaware: 'DE',
  Florida: 'FL',
  Georgia: 'GA',
  Hawaii: 'HI',
  Idaho: 'ID',
  Illinois: 'IL',
  Indiana: 'IN',
  Iowa: 'IA',
  Kansas: 'KS',
  Kentucky: 'KY',
  Louisiana: 'LA',
  Maine: 'ME',
  Maryland: 'MD',
  Massachusetts: 'MA',
  Michigan: 'MI',
  Minnesota: 'MN',
  Mississippi: 'MS',
  Missouri: 'MO',
  Montana: 'MT',
  Nebraska: 'NE',
  Nevada: 'NV',
  'New Hampshire': 'NH',
  'New Jersey': 'NJ',
  'New Mexico': 'NM',
  'New York': 'NY',
  'North Carolina': 'NC',
  'North Dakota': 'ND',
  Ohio: 'OH',
  Oklahoma: 'OK',
  Oregon: 'OR',
  Pennsylvania: 'PA',
  'Rhode Island': 'RI',
  'South Carolina': 'SC',
  'South Dakota': 'SD',
  Tennessee: 'TN',
  Texas: 'TX',
  Utah: 'UT',
  Vermont: 'VT',
  Virginia: 'VA',
  Washington: 'WA',
  'West Virginia': 'WV',
  Wisconsin: 'WI',
  Wyoming: 'WY',
  'District of Columbia': 'DC',
}

const stateAbbreviation = (stateName) => STATE_ABBREVIATIONS[stateName] || 'US'

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
  // Softer scaling prevents ODIN aggregate totals from being pinned at 100.
  return Math.min(100, Math.round(Math.log10(1 + meters) * 12))
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

const normalizeSeverity = (value) => {
  const v = (value || '').toString().toLowerCase()
  if (v.includes('extreme') || v.includes('severe') || v.includes('critical')) return 'high'
  if (v.includes('moderate') || v.includes('medium')) return 'medium'
  if (v.includes('minor') || v.includes('low')) return 'low'
  return 'medium'
}

const blendScore = (previousScore, incomingScore, incomingWeight = 0.5) => {
  const prev = Number.isFinite(previousScore) ? previousScore : 0
  const next = Number.isFinite(incomingScore) ? incomingScore : 0
  const weight = Math.min(1, Math.max(0, incomingWeight))

  if (prev <= 0) return Math.round(next)

  const blended = (prev * (1 - weight)) + (next * weight)
  return Math.max(0, Math.min(100, Math.round(blended)))
}

function App() {
  const [dashboard, setDashboard] = useState({
    score: 0,
    regions: [],
    stressScoreHistory: [],
    riskFactors: [],
    incidents: [],
    disasterIncidents: [],
    sectorAlerts: [],
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [nlpLoading, setNlpLoading] = useState(false)
  const [nlpError, setNlpError] = useState('')
  const [backendConnected, setBackendConnected] = useState(false)
  const [csvRefreshLoading, setCsvRefreshLoading] = useState(false)
  const [csvRefreshMessage, setCsvRefreshMessage] = useState('')
  const [suggestionLoading, setSuggestionLoading] = useState(false)
  const [suggestionError, setSuggestionError] = useState('')
  const [latestSuggestion, setLatestSuggestion] = useState(null)

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
          const state = r.state || 'Unknown State'

          return {
            id: `${utility}-${county}-${index}`,
            meters,
            timestamp,
            status,
            cause,
            utility,
            county,
            state,
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
          region: `${x.county}, ${stateAbbreviation(x.state)}`,
        }))

        let disasterIncidents = []
        let highDisasterCount = 0
        try {
          const disasterEvents = await fetchDisasterEvents()
          disasterIncidents = (Array.isArray(disasterEvents) ? disasterEvents : []).slice(0, 20).map((evt, idx) => {
            const severity = normalizeSeverity(evt.severity)
            if (severity === 'high') highDisasterCount += 1
            return {
              id: `disaster-${idx}-${evt.source || 'api'}`,
              timestamp: toIsoOrNow(evt.timestamp),
              text: evt.description || `${evt.event_type || 'Event'} reported in ${evt.region || 'Unknown region'}`,
              eventType: evt.event_type || 'Natural Disaster',
              cause: evt.source || 'Natural hazard',
              severity,
              region: evt.region || 'Unknown region',
            }
          })
        } catch (evtErr) {
          console.warn('Natural disaster events unavailable:', evtErr)
        }

        const byCounty = normalized.reduce((acc, x) => {
          const key = `${x.county}, ${x.state}`
          if (!acc[key]) {
            acc[key] = { meters: 0, county: x.county, state: x.state }
          }
          acc[key].meters += x.meters
          return acc
        }, {})

        const regionsLive = Object.values(byCounty)
          .sort((a, b) => b.meters - a.meters)
          .slice(0, 4)
          .map((entry, idx) => {
            const countyScore = scoreFromMeters(entry.meters)
            return {
              id: `county-${idx}`,
              name: `${entry.county} County`,
              abbreviation: stateAbbreviation(entry.state),
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

        const totalSignals = Math.max(1, plannedCount + pendingCount + highImpactCount + highDisasterCount)
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
          {
            factor: 'High-severity natural disaster signals',
            contribution: Math.round((highDisasterCount / totalSignals) * 100),
            severity: highDisasterCount > 10 ? 'high' : highDisasterCount > 0 ? 'medium' : 'low',
          },
        ]

        const topCounty = regionsLive[0]?.name || 'United States'
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

        if (highDisasterCount > 0) {
          alertsLive.unshift({
            sector: 'State Emergency Management',
            region: 'Multi-region',
            recommendation: `Monitor ${highDisasterCount} high-severity natural disaster signal(s) from NOAA/FIRMS feeds.`,
            priority: highDisasterCount > 5 ? 'high' : 'medium',
          })
        }

        setDashboard((prev) => {
          const nlpIncidents = prev.incidents.filter((inc) => String(inc.id).startsWith('nlp-'))
          const mergedIncidents = [...nlpIncidents, ...incidentsLive].slice(0, 30)

          return {
            // Live telemetry should steer score strongly while still smoothing jumps.
            score: blendScore(prev.score, score, 0.65),
            regions: regionsLive.length ? regionsLive : regions,
            stressScoreHistory: stressLive.length ? stressLive : stressScoreHistory,
            riskFactors: factorsLive,
            incidents: mergedIncidents,
            disasterIncidents,
            sectorAlerts: alertsLive,
          }
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load live outage data')
        setDashboard({
          score: 78,
          regions,
          stressScoreHistory,
          riskFactors,
          incidents,
          disasterIncidents: [],
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
    setSuggestionError('')
    try {
      const result = await analyzeIncident(text)
      const { incident, risk, alert } = result

      const naturalCauses = ['storm', 'wildfire', 'heatwave', 'hurricane', 'tornado', 'flood']
      const scenarioType = naturalCauses.some((term) => incident.cause?.toLowerCase().includes(term))
        ? 'natural_disaster'
        : 'power_outage'

      setSuggestionLoading(true)
      suggestResponse({
        scenario_type: scenarioType,
        title: `${incident.event_type} in ${incident.region}`,
        description: text,
        region: incident.region,
        severity: incident.severity,
      })
        .then((suggestion) => setLatestSuggestion(suggestion))
        .catch((err) => {
          console.error('Suggestion request failed:', err)
          setSuggestionError(err instanceof Error ? err.message : 'Failed to generate suggestions')
        })
        .finally(() => setSuggestionLoading(false))

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
          // NLP updates nudge score without permanently pinning it at the max.
          const newScore = blendScore(prev.score, score100, 0.35)

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

  const handleRefreshCsv = async () => {
    setCsvRefreshLoading(true)
    setCsvRefreshMessage('')

    try {
      const result = await refreshDataset({ region: 'USA', hours: 24, output: 'data/outages_latest.csv' })
      setCsvRefreshMessage(`CSV refreshed: ${result.rows_written} rows written.`)
    } catch (err) {
      console.error('CSV refresh failed:', err)
      setCsvRefreshMessage(err instanceof Error ? err.message : 'CSV refresh failed')
    } finally {
      setCsvRefreshLoading(false)
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
          <div className="mt-3 flex items-center gap-3">
            <button
              type="button"
              onClick={handleRefreshCsv}
              disabled={!backendConnected || csvRefreshLoading}
              className="rounded-md border border-cyan-500/50 bg-cyan-500/10 px-3 py-1.5 text-xs font-semibold text-cyan-300 transition hover:bg-cyan-500/20 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {csvRefreshLoading ? 'Refreshing CSV...' : 'Refresh outages_latest.csv'}
            </button>
            {csvRefreshMessage ? (
              <p className="text-xs text-slate-400">{csvRefreshMessage}</p>
            ) : null}
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
          <IncidentInput onAnalyze={handleAnalyzeIncident} loading={nlpLoading || loading} />
          {nlpError && (
            <p className="mt-2 text-sm text-amber-400">
              {nlpError} — Start the backend with: <code className="rounded bg-slate-700 px-1">cd backend && uvicorn main:app --reload</code>
            </p>
          )}

          <div className="mt-4 rounded-xl border border-grid-border bg-grid-card p-4">
            <div className="flex items-center justify-between gap-3">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-slate-300">
                AI Response Suggestions
              </h3>
              {latestSuggestion ? (
                <span className="text-xs text-slate-400">
                  source: {latestSuggestion.provider}{latestSuggestion.used_fallback ? ' (fallback)' : ''}
                </span>
              ) : null}
            </div>

            {suggestionLoading ? (
              <p className="mt-3 text-sm text-cyan-400">Generating recommendations...</p>
            ) : null}

            {suggestionError ? (
              <p className="mt-3 text-sm text-amber-400">{suggestionError}</p>
            ) : null}

            {!suggestionLoading && !latestSuggestion && !suggestionError ? (
              <p className="mt-3 text-sm text-slate-500">
                Analyze an incident above to generate response recommendations here.
              </p>
            ) : null}

            {latestSuggestion ? (
              <div className="mt-3 space-y-3">
                <div className="rounded-lg border border-grid-border bg-slate-900/40 p-3">
                  <p className="text-xs uppercase tracking-wider text-slate-500">Analyzed input</p>
                  <p className="mt-1 text-sm italic leading-relaxed text-slate-300 whitespace-normal break-words">
                    "{latestSuggestion.description}"
                  </p>
                </div>

                <p className="text-sm leading-relaxed text-slate-300 whitespace-normal break-words">
                  {latestSuggestion.assessment}
                </p>
                <ul className="space-y-2">
                  {(latestSuggestion.actions || []).map((item, index) => (
                    <li key={`${item.owner}-${index}`} className="rounded-lg border border-grid-border bg-slate-800/40 p-3">
                      <div className="mb-1 flex items-center justify-between gap-2">
                        <span className="rounded bg-cyan-500/20 px-2 py-0.5 text-xs font-semibold text-cyan-300">{item.priority}</span>
                        <span className="text-xs text-slate-400">{item.owner} • {item.timeframe}</span>
                      </div>
                      <p className="text-sm text-slate-200">{item.action}</p>
                    </li>
                  ))}
                </ul>
                {latestSuggestion.public_message ? (
                  <p className="rounded border border-grid-border bg-slate-900/40 p-2 text-xs text-slate-400">
                    Public message: {latestSuggestion.public_message}
                  </p>
                ) : null}
              </div>
            ) : null}
          </div>
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

        {/* Chart + Incident feed */}
        <div className="mt-6 grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <StressChart data={dashboard.stressScoreHistory} />
          </div>
          <div>
            <IncidentFeed incidents={dashboard.incidents} />
          </div>

          <div className="lg:col-span-3">
            <NaturalDisasterFeed incidents={dashboard.disasterIncidents} />
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
