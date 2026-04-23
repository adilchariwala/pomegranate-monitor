import { useState, useEffect, useCallback } from 'react'
import { fetchLatest, fetchStats, fetchHistory, fetchSensors } from './api.js'
import Dashboard from './components/Dashboard.jsx'

const LATEST_MS  = 5_000   // fast poll — just the latest reading card
const REFRESH_MS = 30_000  // full refresh — stats, history, sensors

export default function App() {
  const [sensors, setSensors]   = useState([])
  const [sensorId, setSensorId] = useState('pomegranate-01')
  const [hours, setHours]       = useState(24)

  const [latest, setLatest]     = useState(null)
  const [stats, setStats]       = useState(null)
  const [history, setHistory]   = useState([])
  const [loading, setLoading]   = useState(false)
  const [dataErr, setDataErr]   = useState(null)

  // ── Fast poll: latest reading only ───────────────────────────────────────
  const pollLatest = useCallback(async (sid) => {
    try {
      setLatest(await fetchLatest(sid))
    } catch {
      // silently skip — full refresh will surface real errors
    }
  }, [])

  // ── Full refresh: stats, history, sensors (+ latest) ────────────────────
  const refresh = useCallback(async (sid, h) => {
    setLoading(true)
    setDataErr(null)
    try {
      const [lat, st, hist, sens] = await Promise.all([
        fetchLatest(sid),
        fetchStats(sid, h),
        fetchHistory(sid, h),
        fetchSensors(),
      ])
      setLatest(lat)
      setStats(st)
      setHistory(hist.readings || [])  // oldest-first (backend sorts ascending when start param is used)
      setSensors(sens.sensors || [])
    } catch (e) {
      setDataErr(e.message)
    } finally {
      setLoading(false)
    }
  }, [])

  // ── Fast 5s poll for latest reading ──────────────────────────────────────
  useEffect(() => {
    const id = setInterval(() => pollLatest(sensorId), LATEST_MS)
    return () => clearInterval(id)
  }, [sensorId, pollLatest])

  // ── Full 30s refresh ──────────────────────────────────────────────────────
  useEffect(() => {
    refresh(sensorId, hours)
    const id = setInterval(() => refresh(sensorId, hours), REFRESH_MS)
    return () => clearInterval(id)
  }, [sensorId, hours, refresh])

  return (
    <Dashboard
      latest={latest}
      stats={stats}
      history={history}
      sensors={sensors}
      sensorId={sensorId}
      setSensorId={sid => { setSensorId(sid); refresh(sid, hours) }}
      hours={hours}
      setHours={h => { setHours(h); refresh(sensorId, h) }}
      loading={loading}
      dataErr={dataErr}
      onRefresh={() => refresh(sensorId, hours)}
    />
  )
}
