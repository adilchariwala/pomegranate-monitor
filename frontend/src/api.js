const BASE = (import.meta.env.VITE_API_URL ?? '') + '/api/v1'

export async function apiFetch(path, apiKey) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'X-API-Key': apiKey }
  })
  if (!res.ok) throw new Error(`API error ${res.status}`)
  return res.json()
}

export const fetchLatest   = (sensorId, key) => apiFetch(`/readings/${sensorId}/latest`, key)
export const fetchStats    = (sensorId, hours, key) => apiFetch(`/sensors/${sensorId}/stats?hours=${hours}`, key)
export const fetchHistory  = (sensorId, hours, key) => {
  const start = new Date(Date.now() - hours * 3600 * 1000).toISOString()
  return apiFetch(`/readings?sensor_id=${sensorId}&start=${start}&limit=2000`, key)
}
export const fetchSensors  = (key) => apiFetch('/sensors', key)
export const fetchHealth   = () => apiFetch('/health', '')
