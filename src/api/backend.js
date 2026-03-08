const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function analyzeIncident(text) {
  const res = await fetch(`${API_BASE}/analyze_and_decide`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function healthCheck() {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) throw new Error('Backend unreachable')
  return res.json()
}

export async function refreshDataset({ region = 'USA', hours = 24, output = 'data/outages_latest.csv' } = {}) {
  const res = await fetch(`${API_BASE}/refresh_dataset`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ region, hours, output }),
  })

  if (!res.ok) {
    throw new Error(await res.text())
  }

  return res.json()
}

export async function fetchDisasterEvents() {
  const res = await fetch(`${API_BASE}/events`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function suggestResponse(payload) {
  const res = await fetch(`${API_BASE}/suggest_response`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getReplayStatus() {
  const res = await fetch(`${API_BASE}/feed/replay/status`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function consumeReplayNext(batchSize = 1) {
  const res = await fetch(`${API_BASE}/feed/replay/next`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ batch_size: batchSize }),
  })

  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function resetReplayCursor() {
  const res = await fetch(`${API_BASE}/feed/replay/reset`, {
    method: 'POST',
  })

  if (!res.ok) throw new Error(await res.text())
  return res.json()
}
