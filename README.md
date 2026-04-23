# Pomegranate Monitor

An end-to-end IoT plant health monitoring system. An ESP32 microcontroller reads four environmental sensors every 30 seconds and POSTs readings to a REST API. A React dashboard renders live sensor values, historical charts, a composite plant health score, and an alerts panel.

---

## Architecture

```
┌─────────────────────────────────────────┐
│  ESP32 Hardware (pomegranate-01)        │
│  ├─ DHT22  → temperature + humidity     │
│  ├─ Capacitive soil sensor → moisture % │
│  └─ LDR (analog) → light lux estimate   │
└────────────────┬────────────────────────┘
                 │ HTTP POST /api/v1/readings
                 │ X-API-Key header
                 │ every 30 seconds
                 ▼
┌─────────────────────────────────────────┐
│  Backend — FastAPI (Python 3.11)        │
│  Hosted on Render (Web Service)         │
│  ├─ Pydantic validation                 │
│  ├─ API-key authentication              │
│  └─ pymongo client                      │
└────────────────┬────────────────────────┘
                 │ pymongo
                 ▼
┌─────────────────────────────────────────┐
│  MongoDB Atlas (cloud-hosted)           │
│  Database: pomegranate_monitor          │
│  ├─ readings collection (30-day TTL)    │
│  └─ sensors collection                  │
└─────────────────────────────────────────┘
                 ▲
                 │ HTTPS
┌─────────────────────────────────────────┐
│  Frontend — React 18 + Recharts + Vite  │
│  Hosted on Render (Static Site)         │
│  ├─ Login screen (API key auth)         │
│  ├─ ReadingCards (live values)          │
│  ├─ HealthPanel (score + alerts)        │
│  └─ ChartPanel (time-series charts)     │
└─────────────────────────────────────────┘
```

---

## Sensors

| Sensor | Pin | Measurement | Notes |
|--------|-----|-------------|-------|
| DHT22 | GPIO 4 | Temperature (°C), Humidity (%) | Requires 10kΩ pull-up on data line |
| Capacitive soil sensor | GPIO 34 | Soil moisture (0–100%) | Analog; 12-bit ADC |
| LDR | GPIO 35 | Light (estimated lux) | Linear approximation; not physically calibrated |

---

## Repository Layout

```
pomegranate-monitor/
├── docker-compose.yml          # Local dev stack
├── .env                        # API_KEY (not committed)
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # FastAPI routes
│       ├── models.py           # Pydantic models + health score
│       ├── database.py         # MongoDB client + index setup
│       └── config.py           # pydantic-settings configuration
├── firmware/
│   ├── pomegranate_monitor.ino # ESP32 Arduino sketch
│   └── secrets.h               # WiFi + API credentials (gitignored)
├── frontend/
│   ├── vite.config.js
│   ├── package.json
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       └── components/
│           ├── Dashboard.jsx
│           ├── ReadingCards.jsx
│           ├── ChartPanel.jsx
│           └── HealthPanel.jsx
└── spec/                       # Full technical specification
```

---

## Deploying to Production

The production stack uses three managed services — no servers to provision.

### 1. MongoDB Atlas

1. Create a free cluster at [mongodb.com/atlas](https://www.mongodb.com/atlas).
2. Create a database user with read/write access.
3. Copy the connection string (`mongodb+srv://user:pass@cluster.mongodb.net/`).
4. Under **Network Access**, add `0.0.0.0/0` to allow connections from Render.

### 2. Backend — Render Web Service

1. Create a new **Web Service** on [render.com](https://render.com), connected to this repository.
2. Set the root directory to `backend/`.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add the following environment variables in the Render dashboard:

| Variable        | Value |
|-----------------|-------|
| `MONGODB_URL`   | Your Atlas connection string |
| `DATABASE_NAME` | `pomegranate_monitor` |
| `API_KEY`       | A strong random secret (must also go into `firmware/secrets.h`) |
| `DEBUG`         | `false` |

6. Deploy. Note the public URL (e.g. `https://pomegranate-monitor-api.onrender.com`).

### 3. Frontend — Render Static Site

1. Create a new **Static Site** on Render, connected to this repository.
2. Set the root directory to `frontend/`.
3. Build command: `npm install && npm run build`
4. Publish directory: `dist`
5. Add the environment variable:

| Variable            | Value |
|---------------------|-------|
| `VITE_API_BASE_URL` | `https://<your-backend-url>/api/v1` |

6. Deploy. Render provides HTTPS automatically.

### 4. Flash the Firmware

Update `firmware/secrets.h` with your live backend URL, then reflash:

```c
#define WIFI_SSID     "YourNetworkName"
#define WIFI_PASSWORD "YourPassword"
#define API_KEY       "your-api-key-here"
#define API_URL       "https://pomegranate-monitor-api.onrender.com/api/v1/readings"
```

See [Flashing the ESP32](#flashing-the-esp32) below.

---

## Running Locally

Docker Compose runs the full stack (backend + frontend + local MongoDB) on your machine.

### Prerequisites

- Docker Desktop installed
- A `.env` file at the project root:

```env
API_KEY=your-secret-api-key-here
```

### Start

```bash
docker compose up --build -d
```

- Frontend: `http://localhost:80`
- Backend API: `http://localhost:8000/api/v1`
- MongoDB: `mongodb://mongo:27017` (internal only)

### Stop

```bash
docker compose down        # stop, keep data
docker compose down -v     # stop and delete all data
```

---

## Flashing the ESP32

1. Install Arduino IDE 2.0 or later.
2. Add the ESP32 board package: **Preferences → Additional Board Manager URLs** → add the Espressif ESP32 URL.
3. Install **DHT sensor library** by Adafruit via Library Manager.
4. Copy `firmware/secrets.h.example` to `firmware/secrets.h` and fill in your credentials.
5. Open `firmware/pomegranate_monitor.ino`.
6. Select board: **ESP32 Dev Module** (or your specific variant).
7. Select the correct COM port.
8. Click **Upload**.
9. Open Serial Monitor at **115200 baud** to verify sensor readings and POST responses.

---

## API Reference

All endpoints are under `/api/v1`. Authentication uses the `X-API-Key` header (except `/health`).

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Backend + database status |
| POST | `/readings` | Yes | Ingest a sensor reading (called by ESP32) |
| GET | `/readings` | Yes | List readings with optional filters (`sensor_id`, `start`, `end`, `limit`, `offset`) |
| GET | `/readings/{sensor_id}/latest` | Yes | Most recent reading for a sensor |
| GET | `/sensors` | Yes | List all registered sensors |
| GET | `/sensors/{sensor_id}/stats` | Yes | Aggregated stats + health score over a time window |

Example POST body (sent by ESP32):

```json
{
  "sensor_id":     "pomegranate-01",
  "temperature":   24.5,
  "humidity":      52.3,
  "soil_moisture": 41.0,
  "light_lux":     8200.0,
  "location":      "living-room"
}
```

---

## Running Tests

Backend unit tests use pytest with a mocked MongoDB layer.

```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

---

## Maintenance

### Adding a Second Sensor

No backend changes are required. Flash a second ESP32 with a different `SENSOR_ID` in `secrets.h` (e.g. `pomegranate-02`). The backend auto-registers it on the first POST, and it will appear in the dashboard sensor dropdown.

### Data Retention

Readings older than 30 days are automatically deleted by a MongoDB TTL index on the `timestamp` field. The `sensors` collection is not subject to TTL.

### Rotating the API Key

1. Generate a new strong random key.
2. Update `API_KEY` in the Render backend environment variables and redeploy.
3. Update `API_KEY` in `firmware/secrets.h` and reflash the ESP32.
4. Update the key in the browser dashboard (you will be prompted on next login).

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| ESP32 serial shows HTTP 401 | Wrong `API_KEY` in `secrets.h` | Match `API_KEY` in firmware and backend env var |
| ESP32 serial shows HTTP 422 | Sensor read returned NaN or out-of-range value | Check wiring; DHT22 NaN triggers a retry — look for repeated errors |
| Dashboard shows "Authentication failed" | Wrong API key entered in browser | Re-enter the correct key; session storage is cleared on tab close |
| Dashboard panels show error state | Backend unreachable | Check Render service status; verify `VITE_API_BASE_URL` is correct |
| No data in charts | Firmware not POSTing | Check ESP32 serial monitor; verify WiFi and `API_URL` in `secrets.h` |
| Backend unhealthy (`"database": "disconnected"`) | Atlas connection string wrong or IP not whitelisted | Verify `MONGODB_URL` env var; check Atlas Network Access for `0.0.0.0/0` |
| Soil moisture reads 0% or 100% constantly | Sensor not calibrated for your soil | Adjust `SOIL_DRY_VALUE` / `SOIL_WET_VALUE` in `pomegranate_monitor.ino` |

---

## Specification

Full technical documentation is in [spec/](spec/). Start with [spec/00-index.md](spec/00-index.md).
