const BASE = (import.meta.env.VITE_API_URL ?? '') + '/api/v1'

export async function apiFetch(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`API error ${res.status}`)
  return res.json()
}

export const fetchLatest   = (sensorId) => apiFetch(`/readings/${sensorId}/latest`)
export const fetchStats    = (sensorId, hours) => apiFetch(`/sensors/${sensorId}/stats?hours=${hours}`)
export const fetchHistory  = (sensorId, hours) => {
  const start = new Date(Date.now() - hours * 3600 * 1000).toISOString()
  return apiFetch(`/readings?sensor_id=${sensorId}&start=${start}&limit=2000`)
}
export const fetchSensors  = () => apiFetch('/sensors')
export const fetchHealth   = () => apiFetch('/health')
