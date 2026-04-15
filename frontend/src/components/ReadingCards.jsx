function cardClass(metric, value) {
  if (value === null || value === undefined) return ''
  if (metric === 'temperature') {
    if (value < 10 || value > 38) return 'alert-card'
    if (value < 18 || value > 35) return 'warn-card'
    return 'good-card'
  }
  if (metric === 'humidity') {
    if (value < 25 || value > 80) return 'alert-card'
    if (value < 40 || value > 60) return 'warn-card'
    return 'good-card'
  }
  if (metric === 'soil') {
    if (value < 15) return 'alert-card'
    if (value < 30 || value > 70) return 'warn-card'
    return 'good-card'
  }
  if (metric === 'light') {
    if (value < 1000)  return 'alert-card'
    if (value < 5000)  return 'warn-card'
    return 'good-card'
  }
  return ''
}

function fmt(v, decimals = 1) {
  return v !== undefined && v !== null ? Number(v).toFixed(decimals) : '—'
}

function timeSince(ts) {
  if (!ts) return ''
  const secs = Math.floor((Date.now() - new Date(ts).getTime()) / 1000)
  if (secs < 60) return `${secs}s ago`
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`
  return `${Math.floor(secs / 3600)}h ago`
}

export default function ReadingCards({ latest, stats }) {
  const v = latest || {}
  const s = stats || {}

  const cards = [
    {
      label: '🌡 Temperature',
      metric: 'temperature',
      value: v.temperature,
      unit: '°C',
      min: s.temperature?.min,
      max: s.temperature?.max,
    },
    {
      label: '💧 Humidity',
      metric: 'humidity',
      value: v.humidity,
      unit: '%',
      min: s.humidity?.min,
      max: s.humidity?.max,
    },
    {
      label: '🌱 Soil Moisture',
      metric: 'soil',
      value: v.soil_moisture,
      unit: '%',
      min: s.soil_moisture?.min,
      max: s.soil_moisture?.max,
    },
    {
      label: '☀️ Light',
      metric: 'light',
      value: v.light_lux,
      unit: 'lux',
      min: s.light_lux?.min,
      max: s.light_lux?.max,
      decimals: 0,
    },
  ]

  return (
    <div className="cards">
      {cards.map(c => (
        <div key={c.metric} className={`card ${cardClass(c.metric, c.value)}`}>
          <span className="card-label">{c.label}</span>
          <span className="card-value">{fmt(c.value, c.decimals ?? 1)}</span>
          <span className="card-unit">{c.unit}</span>
          {(c.min !== undefined || c.max !== undefined) && (
            <span className="card-sub">
              min {fmt(c.min, c.decimals ?? 1)} · max {fmt(c.max, c.decimals ?? 1)}
            </span>
          )}
          {latest && <span className="card-sub">{timeSince(latest.timestamp)}</span>}
        </div>
      ))}
    </div>
  )
}
