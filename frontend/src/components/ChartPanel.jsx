import { useState } from 'react'
import {
  ResponsiveContainer, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine,
} from 'recharts'

const METRICS = [
  { key: 'temperature',   label: '🌡 Temp (°C)',      color: '#e05252', unit: '°C',  refLow: 18, refHigh: 35 },
  { key: 'humidity',      label: '💧 Humidity (%)',    color: '#3a7bd5', unit: '%',   refLow: 40, refHigh: 60 },
  { key: 'soil_moisture', label: '🌱 Soil Moisture (%)', color: '#4caf72', unit: '%', refLow: 30, refHigh: 60 },
  { key: 'light_lux',    label: '☀️ Light (lux)',     color: '#f0a500', unit: ' lux', refLow: 10000 },
]

function fmtTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function CustomTooltip({ active, payload, label, unit }) {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: '#fff', border: '1.5px solid #e2e8e0',
      borderRadius: 8, padding: '8px 12px', fontSize: '.85rem',
    }}>
      <p style={{ color: '#6b7280', marginBottom: 2 }}>{label}</p>
      <p style={{ fontWeight: 700 }}>{payload[0].value.toFixed(1)}{unit}</p>
    </div>
  )
}

export default function ChartPanel({ history }) {
  const [active, setActive] = useState('temperature')
  const metric = METRICS.find(m => m.key === active)

  const data = history.map(r => ({
    time: fmtTime(r.timestamp),
    value: r[active],
  }))

  return (
    <div className="chart-card">
      <div className="chart-header">
        <h2>Time Series</h2>
        <div className="tab-group">
          {METRICS.map(m => (
            <button key={m.key} className={`tab ${active === m.key ? 'active' : ''}`}
              onClick={() => setActive(m.key)}>
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {data.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--muted)' }}>
          No data for this time window yet.
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={data} margin={{ top: 4, right: 16, left: 0, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="time"
              tick={{ fontSize: 11, fill: '#6b7280' }}
              interval="preserveStartEnd"
            />
            <YAxis tick={{ fontSize: 11, fill: '#6b7280' }} width={48} />
            <Tooltip content={<CustomTooltip unit={metric.unit} />} />
            {metric.refLow && (
              <ReferenceLine y={metric.refLow} stroke={metric.color}
                strokeDasharray="4 2" opacity={0.5}
                label={{ value: 'min', fontSize: 10, fill: metric.color }} />
            )}
            {metric.refHigh && (
              <ReferenceLine y={metric.refHigh} stroke={metric.color}
                strokeDasharray="4 2" opacity={0.5}
                label={{ value: 'max', fontSize: 10, fill: metric.color }} />
            )}
            <Line
              type="monotone"
              dataKey="value"
              stroke={metric.color}
              strokeWidth={2}
              dot={data.length < 60}
              activeDot={{ r: 5 }}
            />
          </LineChart>
        </ResponsiveContainer>
      )}

      <p style={{ fontSize: '.78rem', color: 'var(--muted)', marginTop: '.75rem', textAlign: 'right' }}>
        {data.length} readings · dashed lines = optimal range
      </p>
    </div>
  )
}
