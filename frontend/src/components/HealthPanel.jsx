function scoreColor(score) {
  if (score >= 80) return '#4caf72'
  if (score >= 55) return '#f0a500'
  return '#e05252'
}

function buildAlerts(latest) {
  const alerts = []
  if (!latest) return alerts
  const { temperature: t, humidity: h, soil_moisture: s, light_lux: l } = latest

  if (t !== undefined) {
    if (t < 5)       alerts.push({ icon: '🥶', msg: `Temperature critically low (${t.toFixed(1)}°C) — risk of frost damage` })
    else if (t > 38) alerts.push({ icon: '🔥', msg: `Temperature too high (${t.toFixed(1)}°C) — move plant to shade` })
    else if (t < 18) alerts.push({ icon: '⚠️', msg: `Temperature below optimal range (${t.toFixed(1)}°C)` })
  }
  if (h !== undefined) {
    if (h > 75) alerts.push({ icon: '💦', msg: `High humidity (${h.toFixed(1)}%) — increased disease risk` })
    if (h < 30) alerts.push({ icon: '🏜️', msg: `Low humidity (${h.toFixed(1)}%) — consider humidifier` })
  }
  if (s !== undefined) {
    if (s < 15)      alerts.push({ icon: '🚨', msg: `Soil critically dry (${s.toFixed(1)}%) — water immediately` })
    else if (s < 30) alerts.push({ icon: '💧', msg: `Soil moisture low (${s.toFixed(1)}%) — consider watering soon` })
    else if (s > 75) alerts.push({ icon: '🌊', msg: `Soil too wet (${s.toFixed(1)}%) — risk of root rot` })
  }
  if (l !== undefined) {
    if (l < 1000)  alerts.push({ icon: '🌑', msg: `Very low light (${Math.round(l)} lux) — move to a sunnier spot` })
    else if (l < 5000) alerts.push({ icon: '⛅', msg: `Below-optimal light (${Math.round(l)} lux) — pomegranates need full sun` })
  }
  return alerts
}

export default function HealthPanel({ stats, latest }) {
  const score  = stats?.health_score ?? null
  const alerts = buildAlerts(latest)
  const color  = score !== null ? scoreColor(score) : '#ccc'
  const label  = score === null ? '—'
    : score >= 80 ? '🟢 Thriving'
    : score >= 55 ? '🟡 Needs Attention'
    : '🔴 At Risk'

  return (
    <div className="health-row">
      {/* Score gauge */}
      <div className="health-card">
        <span className="card-label">Plant Health Score</span>
        <span className="health-score-number" style={{ color }}>
          {score !== null ? score : '—'}
        </span>
        <div className="score-bar-wrap">
          <div className="score-bar"
            style={{ width: `${score ?? 0}%`, background: color }} />
        </div>
        <span style={{ fontSize: '.82rem', color: 'var(--muted)', marginTop: '.25rem' }}>
          {label}
        </span>
      </div>

      {/* Alerts */}
      <div className="alerts-card">
        <h3>⚡ Alerts</h3>
        {alerts.length === 0 ? (
          <p className="no-alerts">✅ All readings within healthy ranges.</p>
        ) : (
          alerts.map((a, i) => (
            <div key={i} className="alert-item">
              <span className="alert-icon">{a.icon}</span>
              <span>{a.msg}</span>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
