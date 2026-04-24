# Pomegranate Monitor — System Overview

## Purpose

Pomegranate Monitor is an end-to-end IoT plant health monitoring system. An ESP32 microcontroller reads four environmental sensors and POSTs readings to a REST API every 30 seconds. The API stores readings in MongoDB. A React dashboard renders live sensor values, historical charts, a composite plant health score, and an alerts panel.

---

## Architecture

```
┌─────────────────────────────────────────┐
│  ESP32 Hardware (pomegranate-01)        │
│  ├─ DHT22  → temperature + humidity     │
│  ├─ Soil sensor (analog) → moisture %   │
│  └─ LDR (analog) → light lux estimate   │
└────────────────┬────────────────────────┘
                 │ HTTP POST /api/v1/readings
                 │ X-API-Key header
                 │ every 30 seconds
                 ▼
┌─────────────────────────────────────────┐
│  Backend — FastAPI / Python 3.11        │
│  Port 8000 (Docker)                     │
│  ├─ Pydantic validation                 │
│  ├─ API-key authentication              │
│  └─ pymongo client                      │
└────────────────┬────────────────────────┘
                 │ pymongo
                 ▼
┌─────────────────────────────────────────┐
│  MongoDB 7                              │
│  Database: pomegranate_monitor          │
│  ├─ readings collection (30-day TTL)    │
│  └─ sensors collection                  │
└─────────────────────────────────────────┘
                 ▲
                 │ HTTP (proxied through nginx)
┌─────────────────────────────────────────┐
│  Frontend — React 18 + Recharts + Vite  │
│  Port 80 (Docker, nginx)                │
│  ├─ Login screen (API key auth)         │
│  ├─ ReadingCards (live values)          │
│  ├─ HealthPanel (score + alerts)        │
│  └─ ChartPanel (time-series charts)     │
└─────────────────────────────────────────┘
```

## Service Topology

### Production

Three managed cloud services — no self-hosted infrastructure:

| Layer     | Service                        | Notes |
|-----------|--------------------------------|-------|
| Database  | **MongoDB Atlas**              | Cloud-hosted MongoDB; Atlas connection URI |
| Backend   | **Render** (Web Service)       | FastAPI; auto-deploys from `main` |
| Frontend  | **Render** (Static Site)       | React build served over HTTPS; auto-deploys from `main` |

### Local Development

Three Docker services orchestrated via `docker-compose.yml`:

| Service    | Image                   | Port | Depends On |
|------------|-------------------------|------|------------|
| `mongo`    | `mongo:7`               | —    | —          |
| `backend`  | built from `./backend`  | 8000 | `mongo`    |
| `frontend` | built from `./frontend` | 80   | `backend`  |

MongoDB data persists locally via a named Docker volume (`mongo_data`).

## Key Design Decisions

- **No user accounts.** A single shared API key authenticates all requests (firmware and browser dashboard).
- **Stateless backend.** No sessions. Each request carries `X-API-Key`.
- **Browser stores key in `sessionStorage`** (cleared on tab close).
- **30-day rolling window.** MongoDB TTL index automatically purges readings older than 30 days.
- **Single sensor initially.** The system supports multiple sensors via `sensor_id` but the current firmware sends only `pomegranate-01`.
- **HTTPS in production.** Render provides TLS automatically for both the static site and the backend web service. The ESP32 firmware uses `WiFiClientSecure` when connecting to the production API.
- **Temperature stored in °C.** The frontend ReadingCards component converts to °F for display; all other components and the backend use °C.

## Repository Layout

```
pomegranate-monitor/
├── docker-compose.yml
├── .env                        # API_KEY (not committed to source control)
├── .gitignore
├── README.md
├── spec/                       # This specification
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py             # FastAPI routes
│   │   ├── models.py           # Pydantic models + health score
│   │   ├── database.py         # MongoDB client + index setup
│   │   └── config.py           # pydantic-settings configuration
│   └── tests/
│       ├── conftest.py
│       ├── test_api.py
│       └── test_models.py
├── firmware/
│   ├── pomegranate_monitor.ino # ESP32 Arduino sketch
│   └── secrets.h               # WiFi + API credentials (gitignored)
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── vite.config.js
    ├── package.json
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── api.js
        ├── index.css
        └── components/
            ├── Dashboard.jsx
            ├── ReadingCards.jsx
            ├── ChartPanel.jsx
            └── HealthPanel.jsx
```
