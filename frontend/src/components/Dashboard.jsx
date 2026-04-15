import ReadingCards from './ReadingCards.jsx'
import HealthPanel from './HealthPanel.jsx'
import ChartPanel from './ChartPanel.jsx'

export default function Dashboard({
  latest, stats, history, sensors,
  sensorId, setSensorId, hours, setHours,
  loading, dataErr, onRefresh, onLogout,
}) {
  const online = latest
    ? (Date.now() - new Date(latest.timestamp).getTime()) < 120_000
    : false

  return (
    <>
      <header className="app-header">
        <h1>🌱 Pomegranate Monitor</h1>
        <div className="header-right">
          <span style={{ fontSize: '.85rem', opacity: .85 }}>
            <span className={`status-dot ${online ? 'online' : ''}`} />
            {online ? 'Live' : 'Offline'}
          </span>
          <button className="btn-sm" onClick={onRefresh} disabled={loading}>
            {loading ? '…' : '↺ Refresh'}
          </button>
          <button className="btn-sm" onClick={onLogout}>Logout</button>
        </div>
      </header>

      <main className="main">
        {/* Sensor + time selector */}
        <div className="sensor-bar">
          <label>Sensor</label>
          <select value={sensorId} onChange={e => setSensorId(e.target.value)}>
            {sensors.length
              ? sensors.map(s => <option key={s.sensor_id} value={s.sensor_id}>{s.sensor_id}</option>)
              : <option value={sensorId}>{sensorId}</option>}
          </select>
          <label style={{ marginLeft: '1rem' }}>Window</label>
          {[6, 24, 48, 168].map(h => (
            <button key={h} className={`tab ${hours === h ? 'active' : ''}`}
              onClick={() => setHours(h)}>
              {h < 24 ? `${h}h` : h === 168 ? '7d' : `${h / 24}d`}
            </button>
          ))}
        </div>

        {dataErr && (
          <div className="error-box" style={{ margin: '2rem auto' }}>
            <strong>Could not load data</strong><br />{dataErr}
          </div>
        )}

        {!dataErr && (
          <>
            <ReadingCards latest={latest} stats={stats} />
            <HealthPanel stats={stats} latest={latest} />
            <ChartPanel history={history} />
          </>
        )}
      </main>
    </>
  )
}
