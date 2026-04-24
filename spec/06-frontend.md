# Pomegranate Monitor — Frontend Specification

## Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| React      | 18.3    | UI framework |
| Recharts   | 2.12    | Time-series charts |
| Vite       | 5.4     | Dev server + build tool |
| nginx      | alpine  | Production static file server + API proxy |

No TypeScript. No state management library (useState/useEffect only).

---

## Entry Points

| File                  | Role |
|-----------------------|------|
| `index.html`          | HTML shell; mounts `<div id="root">` |
| `src/main.jsx`        | `ReactDOM.createRoot` mount |
| `src/App.jsx`         | Root component; owns all state and data fetching |
| `src/index.css`       | All CSS (CSS custom properties, responsive layout) |

---

## Authentication Flow

1. On app load, check `sessionStorage.getItem('pmKey')`.
2. If null → render `<LoginScreen>` (inline in `App.jsx`):
   - Input field for API key.
   - On submit: call `GET /api/v1/health` with `X-API-Key: <entered_key>`. Note: the health endpoint does not actually validate the key, so the frontend calls it as a connectivity check. The real validation happens on the first protected API call.
   - On success (HTTP 200): store key in `sessionStorage` and re-render dashboard.
   - On failure: show error message "Authentication failed".
3. If key present → render `<Dashboard>` directly.
4. Logout button: `sessionStorage.removeItem('pmKey')` → re-render login screen.

---

## Component Tree

```
App
├── LoginScreen (inline, conditional)
└── Dashboard
    ├── Header
    │   ├── LiveStatusDot
    │   ├── SensorDropdown
    │   ├── TimeWindowTabs (6h | 24h | 48h | 7d)
    │   ├── RefreshButton
    │   └── LogoutButton
    ├── ReadingCards (4 cards)
    ├── HealthPanel
    │   ├── HealthGauge (score + label)
    │   └── AlertsList
    └── ChartPanel
        ├── MetricTabs (temperature | humidity | soil | light)
        └── RechartsLineChart
```

---

## State (App.jsx)

| State variable | Type    | Description |
|----------------|---------|-------------|
| `apiKey`       | string  | From sessionStorage; null if not logged in |
| `sensorId`     | string  | Currently selected sensor_id |
| `hours`        | int     | Time window in hours (6, 24, 48, 168) |
| `latest`       | object  | Response from `GET /readings/{sensorId}/latest` |
| `stats`        | object  | Response from `GET /sensors/{sensorId}/stats` |
| `history`      | array   | Response from `GET /readings`, reversed to oldest-first for chart rendering |
| `sensors`      | array   | Response from `GET /sensors` |
| `loading`      | boolean | True while any fetch is in progress |
| `dataErr`      | string  | Error message if fetch fails |

**Auto-refresh:** `setInterval` every 30,000ms calls `fetchAllData()`. Interval is cleared on component unmount.

---

## API Client (`src/api.js`)

Base URL: `/api/v1` (relative path; proxied by nginx in production, by Vite dev proxy in development).

All functions receive `apiKey` and inject the `X-API-Key` header.

| Function | HTTP Call | Notes |
|----------|-----------|-------|
| `fetchLatest(apiKey, sensorId)` | `GET /readings/{sensorId}/latest` | Returns null on 404 |
| `fetchStats(apiKey, sensorId, hours)` | `GET /sensors/{sensorId}/stats?hours={hours}` | Returns null on 404 |
| `fetchHistory(apiKey, sensorId, hours)` | `GET /readings?sensor_id={sensorId}&start={iso}&limit=500` | Calculates `start = now - hours`; returns array |
| `fetchSensors(apiKey)` | `GET /sensors` | Returns array |
| `fetchHealth(apiKey)` | `GET /health` | Sends empty string as key (health is unauthed) |

---

## Component Specifications

### Dashboard.jsx

- Sticky header with: app title, live status dot, sensor dropdown, time-window tabs (6h / 24h / 48h / 7d), Refresh button, Logout button.
- **Live status dot:** green if `latest.timestamp` is within the last 2 minutes of browser local time; grey otherwise. Label: "Live" / "Offline".
- **Sensor dropdown:** populated from `sensors` array; defaults to first sensor on load or after sensor list refreshes.
- **Time window tabs:** clicking a tab updates `hours` state and triggers a data re-fetch.
- Main content area: 2-column grid (ReadingCards + HealthPanel on top, ChartPanel full-width below) on desktop; stacks to single-column on mobile.

### ReadingCards.jsx

Four cards, one per metric. Each card shows:
- Metric name and icon
- Current value (from `latest`)
- Period min / max (from `stats`)
- Color-coded background: green / yellow / red based on thresholds (see Data Models spec)
- "Last updated N minutes ago" label using `timeSince(latest.timestamp)`

**Temperature display:** Stored and returned in °C; displayed in °F. Conversion: `°F = °C * 9/5 + 32`.

**`timeSince` note:** The current implementation subtracts 4 hours to approximate Eastern time. This is a hardcoded hack; a robust implementation should use the `Intl` API or `date-fns-tz`.

### HealthPanel.jsx

- **Health gauge:** Large number (0–100) + status label ("Thriving" / "Needs Attention" / "At Risk") + color.
- **Alert list:** Scrollable. Each alert message describes which metric is outside the threshold and by how much. Derived from `latest` reading. Examples:
  - "Soil moisture is critically low (12%)"
  - "Temperature is high (38.5°C)"
  - "Light is low (800 lux) — plant may not be getting enough sun"
- If no alerts: show "All readings are within acceptable ranges".

### ChartPanel.jsx

- Tab selector for metric: Temperature (°C) | Humidity (%) | Soil Moisture (%) | Light (lux).
- Recharts `LineChart` with `ResponsiveContainer`.
- X-axis: `timestamp` formatted as `HH:mm` (America/New_York timezone). For the 7-day window, format as `MM/dd HH:mm`.
- Y-axis: auto-domain with a small padding.
- `history` array is passed in oldest-first order (reversed from API response).
- Dashed reference lines mark optimal range boundaries:

| Metric         | Reference lines (dashed) |
|----------------|--------------------------|
| Temperature    | 18°C, 35°C              |
| Humidity       | 40%, 60%                 |
| Soil Moisture  | 30%, 60%                 |
| Light          | 5,000 lux               |

- Dots (`dot={true}`) only when the dataset has fewer than 60 data points; otherwise `dot={false}` for performance.
- Tooltip shows formatted value + timestamp on hover.

---

## Vite Dev Proxy (`vite.config.js`)

```js
server: {
  proxy: {
    '/api': 'http://localhost:8000'
  }
}
```

This mirrors the nginx proxy behavior in production, so the frontend can be developed with `npm run dev` against a locally-running backend.

---

## nginx Configuration (`nginx.conf`)

```nginx
server {
    listen 80;

    location / {
        root   /usr/share/nginx/html;
        index  index.html;
        try_files $uri $uri/ /index.html;   # SPA client-side routing
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

- All non-API requests fall through to `index.html` for client-side routing.
- `/api/` requests are proxied to the `backend` Docker service on port 8000.

---

## Build

```bash
# Development
npm install
npm run dev        # Vite dev server on :5173 with API proxy

# Production (via Docker)
docker compose up --build
```

The production Docker build is multi-stage:
1. `node:20-alpine` → `npm install && npm run build` → outputs to `/app/dist`
2. `nginx:alpine` → copies `/app/dist` to `/usr/share/nginx/html`, copies `nginx.conf`
