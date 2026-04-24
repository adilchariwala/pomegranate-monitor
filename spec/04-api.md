# Pomegranate Monitor — API Specification

## Base URL

In production (Docker): `http://<host>/api/v1`  
In development (Vite proxy): `http://localhost:5173/api/v1` → proxied to `http://localhost:8000/api/v1`

All paths below are relative to `/api/v1`.

---

## Authentication

All endpoints except `GET /health` require the header:

```
X-API-Key: <api_key>
```

The API key is configured via the `API_KEY` environment variable on the backend. A missing or incorrect key returns:

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json

{
  "detail": "Invalid or missing API key"
}
```

---

## Endpoints

### GET /health

Check backend and database status. **No authentication required.**

**Response 200:**
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-04-20T14:32:00Z"
}
```

**Response 200 (database unreachable):**
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "timestamp": "2026-04-20T14:32:00Z"
}
```

---

### POST /readings

Ingest a new sensor reading. Called by the ESP32 firmware every 30 seconds.

**Headers:**
```
Content-Type: application/json
X-API-Key: <api_key>
```

**Request body:**
```json
{
  "sensor_id":    "pomegranate-01",
  "temperature":  24.5,
  "humidity":     52.3,
  "soil_moisture": 41.0,
  "light_lux":    8200.0,
  "timestamp":    "2026-04-20T14:32:00Z",
  "location":     "living-room"
}
```

| Field          | Type   | Required | Constraints                              |
|----------------|--------|----------|------------------------------------------|
| `sensor_id`    | string | yes      | 1–50 chars, `^[a-zA-Z0-9-]+$`            |
| `temperature`  | float  | yes      | -40.0 to 85.0 (°C)                       |
| `humidity`     | float  | yes      | 0.0 to 100.0 (%)                         |
| `soil_moisture`| float  | yes      | 0.0 to 100.0 (%)                         |
| `light_lux`    | float  | yes      | 0.0 to 200,000.0                         |
| `timestamp`    | string | no       | ISO 8601 UTC; auto-filled to `now()` if absent |
| `location`     | string | no       | max 100 chars                            |

**Response 201:**
```json
{
  "id":            "66a1b2c3d4e5f6a7b8c9d0e1",
  "sensor_id":     "pomegranate-01",
  "temperature":   24.5,
  "humidity":      52.3,
  "soil_moisture": 41.0,
  "light_lux":     8200.0,
  "timestamp":     "2026-04-20T14:32:00Z",
  "location":      "living-room"
}
```

**Response 401:** Missing or invalid API key.  
**Response 422:** Pydantic validation error (out-of-range value, invalid sensor_id format, missing required field). Body is FastAPI's default validation error format.

---

### GET /readings

Retrieve a paginated, optionally filtered list of readings sorted newest-first.

**Query parameters:**

| Parameter   | Type   | Required | Default | Constraints          | Description                            |
|-------------|--------|----------|---------|----------------------|----------------------------------------|
| `sensor_id` | string | no       | —       | —                    | Filter by sensor ID                    |
| `start`     | string | no       | —       | ISO 8601 datetime    | Only readings at or after this time    |
| `end`       | string | no       | —       | ISO 8601 datetime    | Only readings at or before this time   |
| `limit`     | int    | no       | 100     | 1–1000               | Max number of results                  |
| `offset`    | int    | no       | 0       | ≥ 0                  | Number of results to skip              |

**Response 200:**
```json
[
  {
    "id":            "66a1b2c3d4e5f6a7b8c9d0e1",
    "sensor_id":     "pomegranate-01",
    "temperature":   24.5,
    "humidity":      52.3,
    "soil_moisture": 41.0,
    "light_lux":     8200.0,
    "timestamp":     "2026-04-20T14:32:00Z",
    "location":      "living-room"
  }
]
```

Returns an empty array `[]` if no documents match. Results are sorted `timestamp DESC`.

**Response 401:** Missing or invalid API key.

---

### GET /readings/{sensor_id}/latest

Retrieve the single most recent reading for a sensor.

**Path parameter:** `sensor_id` — the sensor identifier.

**Response 200:**
```json
{
  "id":            "66a1b2c3d4e5f6a7b8c9d0e1",
  "sensor_id":     "pomegranate-01",
  "temperature":   24.5,
  "humidity":      52.3,
  "soil_moisture": 41.0,
  "light_lux":     8200.0,
  "timestamp":     "2026-04-20T14:32:00Z",
  "location":      "living-room"
}
```

**Response 401:** Missing or invalid API key.  
**Response 404:** No readings exist for this sensor. Body: `{"detail": "No readings found for sensor pomegranate-01"}`.

---

### GET /sensors

List all registered sensors, sorted by `last_seen` descending.

**Response 200:**
```json
[
  {
    "sensor_id":     "pomegranate-01",
    "location":      "living-room",
    "registered_at": "2026-03-01T10:00:00Z",
    "last_seen":     "2026-04-20T14:32:00Z"
  }
]
```

Returns an empty array `[]` if no sensors registered.

**Response 401:** Missing or invalid API key.

---

### GET /sensors/{sensor_id}/stats

Retrieve aggregated statistics and a plant health score for a sensor over a rolling time window.

**Path parameter:** `sensor_id` — the sensor identifier.

**Query parameters:**

| Parameter | Type | Required | Default | Constraints | Description                        |
|-----------|------|----------|---------|-------------|------------------------------------|
| `hours`   | int  | no       | 24      | 1–720       | Number of hours to look back       |

**Response 200:**
```json
{
  "sensor_id":     "pomegranate-01",
  "period_hours":  24,
  "temperature":   { "min": 20.1, "max": 27.3, "avg": 23.8 },
  "humidity":      { "min": 45.0, "max": 61.2, "avg": 52.3 },
  "soil_moisture": { "min": 38.0, "max": 45.0, "avg": 41.5 },
  "light_lux":     { "min": 0.0,  "max": 9800.0, "avg": 4200.0 },
  "reading_count": 2880,
  "health_score":  78.5
}
```

The `health_score` is computed from the average values of each metric using the algorithm defined in the Data Models spec.

**Response 401:** Missing or invalid API key.  
**Response 404:** No readings exist for this sensor in the requested time window.

---

## Error Response Format

FastAPI returns validation errors in its default format. Application-level errors use:

```json
{
  "error":   "not_found",
  "message": "No readings found for sensor pomegranate-01",
  "details": null
}
```

---

## Rate Limiting

No rate limiting is implemented. The backend accepts requests at any rate.

---

## CORS

The backend allows all origins (`*`) on all methods and headers. This is appropriate for a local/personal deployment but must be tightened for any public-facing cloud deployment.

---

## Versioning

All routes are under `/api/v1`. No other versions exist.
