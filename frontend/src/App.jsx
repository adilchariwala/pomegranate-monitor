import { useState, useEffect, useCallback } from 'react'
import { fetchLatest, fetchStats, fetchHistory, fetchSensors } from './api.js'
import Dashboard from './components/Dashboard.jsx'

const REFRESH_MS = 30_000

export default function App() {
  const [apiKey, setApiKey]       = useState(sessionStorage.getItem('pmKey') || '')
  const [keyInput, setKeyInput]   = useState('')
  const [authErr, setAuthErr]     = useState(false)
  const [logging, setLogging]     = useState(false)

  const [sensors, setSensors]     = useState([])
  const [sensorId, setSensorId]   = useState('pomegranate-01')
  const [hours, setHours]         = useState(24)

  const [latest, setLatest]       = useState(null)
  const [stats, setStats]         = useState(null)
  const [history, setHistory]     = useState([])
  const [loading, setLoading]     = useState(false)
  const [dataErr, setDataErr]     = useState(null)

  // ── Fetch all dashboard data ─────────────────────────────────────────────
  const refresh = useCallback(async (key, sid, h) => {
    setLoading(true)
    setDataErr(null)
    try {
      const [lat, st, hist, sens] = await Promise.all([
        fetchLatest(sid, key),
        fetchStats(sid, h, key),
        fetchHistory(sid, h, key),
        fetchSensors(key),
      ])
      setLatest(lat)
      setStats(st)
      setHistory((hist.readings || []).reverse())  // oldest first for chart
      setSensors(sens.sensors || [])
    } catch (e) {
      setDataErr(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  // ── Auto-refresh ─────────────────────────────────────────────────────────
  useEffect(() => {
    if (!apiKey) return
    refresh(apiKey, sensorId, hours)
    const id = setInterval(() => refresh(apiKey, sensorId, hours), REFRESH_MS)
    return () => clearInterval(id)
  }, [apiKey, sensorId, hours, refresh])

  // ── Login ────────────────────────────────────────────────────────────────
  async function handleLogin(e) {
    e.preventDefault()
    setLogging(true)
    setAuthErr(false)
    try {
      await fetchLatest(sensorId, keyInput)
      sessionStorage.setItem('pmKey', keyInput)
      setApiKey(keyInput)
    } catch {
      setAuthErr(true)
    } finally {
      setLogging(false)
    }
  }

  if (!apiKey) {
    return (
      <div className="login-wrap">
        <div className="login-card">
          <h1>🌱 Pomegranate Monitor</h1>
          <p>Enter your API key to access the dashboard</p>
          <form onSubmit={handleLogin}>
            <input
              type="password"
              placeholder="API Key"
              value={keyInput}
              onChange={e => setKeyInput(e.target.value)}
              className={authErr ? 'err' : ''}
              autoFocus
            />
            {authErr && <p className="errmsg">Invalid API key — check your .env and try again.</p>}
            <button className="btn-primary" disabled={!keyInput || logging}>
              {logging ? 'Connecting…' : 'Connect'}
            </button>
          </form>
        </div>
      </div>
    )
  }

  return (
    <Dashboard
      latest={latest}
      stats={stats}
      history={history}
      sensors={sensors}
      sensorId={sensorId}
      setSensorId={sid => { setSensorId(sid); refresh(apiKey, sid, hours) }}
      hours={hours}
      setHours={h => { setHours(h); refresh(apiKey, sensorId, h) }}
      loading={loading}
      dataErr={dataErr}
      onRefresh={() => refresh(apiKey, sensorId, hours)}
      onLogout={() => { sessionStorage.removeItem('pmKey'); setApiKey('') }}
    />
  )
}
