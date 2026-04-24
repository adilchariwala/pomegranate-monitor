# Pomegranate Monitor — Deployment Specification

## Production Deployment (Current)

The system is deployed across three managed services — no self-hosted infrastructure required.

| Layer     | Service                        | Notes |
|-----------|--------------------------------|-------|
| Database  | **MongoDB Atlas** (M0 free tier) | Cloud-hosted MongoDB; connection via Atlas URI |
| Backend   | **Render** (Web Service)       | Runs the FastAPI app; auto-deploys from `main` branch |
| Frontend  | **Render** (Static Site)       | Serves the built React app; auto-deploys from `main` branch |

---

### MongoDB Atlas

- Cluster hosted on MongoDB Atlas (free M0 tier or higher).
- The backend connects via an Atlas connection string set in the `MONGODB_URL` environment variable on Render.
- IP access list on Atlas must include `0.0.0.0/0` (allow all) **or** the static outbound IPs of the Render backend service.
- Database name: `pomegranate_monitor`
- Collections: `readings` (30-day TTL index on `timestamp`), `sensors`

### Backend — Render Web Service

- **Build command:** `pip install -r requirements.txt`
- **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Environment variables** (set in Render dashboard):

| Variable        | Description |
|-----------------|-------------|
| `MONGODB_URL`   | MongoDB Atlas connection string (e.g. `mongodb+srv://user:pass@cluster.mongodb.net/`) |
| `DATABASE_NAME` | `pomegranate_monitor` |
| `API_KEY`       | Shared secret for API authentication; must match `firmware/secrets.h` |
| `DEBUG`         | `false` in production |

- Auto-deploys when `main` branch is pushed.
- Public URL is the backend API base (e.g. `https://pomegranate-monitor-api.onrender.com`).

### Frontend — Render Static Site

- **Build command:** `npm install && npm run build`
- **Publish directory:** `dist`
- **Environment variables** (set in Render dashboard):

| Variable            | Description |
|---------------------|-------------|
| `VITE_API_BASE_URL` | Full URL of the backend service (e.g. `https://pomegranate-monitor-api.onrender.com/api/v1`) |

- Auto-deploys when `main` branch is pushed.
- Served over HTTPS by default (Render provides TLS automatically).

---

## Firmware Update for Production

After deploying, update `firmware/secrets.h` with the live backend URL and reflash the ESP32:

```c
#define API_URL "https://pomegranate-monitor-api.onrender.com/api/v1/readings"
```

Use `WiFiClientSecure` for HTTPS connections from the ESP32.

---

## Local Development

For local development, Docker Compose can still be used to run the full stack locally.

### Prerequisites

- Docker Desktop (or Docker Engine + Compose plugin) installed
- A `.env` file at the project root

### `.env` file

```env
API_KEY=your-secret-api-key-here
```

### Start the stack

```bash
docker compose up --build -d
```

- Frontend: `http://localhost:80`
- Backend API: `http://localhost:8000/api/v1`
- MongoDB: accessible internally at `mongodb://mongo:27017`

### Stop and clean up

```bash
docker compose down          # stop containers, preserve mongo_data volume
docker compose down -v       # stop containers AND delete all data
```

---

## Environment Variables Reference

| Variable            | Required | Default               | Description |
|---------------------|----------|-----------------------|-------------|
| `MONGODB_URL`       | yes      | —                     | MongoDB Atlas URI (production) or `mongodb://mongo:27017` (local) |
| `DATABASE_NAME`     | no       | `pomegranate_monitor` | MongoDB database name |
| `API_KEY`           | yes      | —                     | Shared secret for API authentication |
| `DEBUG`             | no       | `false`               | Enables FastAPI debug mode (verbose errors) |
| `VITE_API_BASE_URL` | yes (frontend) | — | Backend API base URL, injected at build time by Vite |

---

## Health Monitoring

The `/api/v1/health` endpoint can be polled by any uptime monitoring service (e.g., UptimeRobot, Betterstack):

- **URL:** `https://<render-backend-url>/api/v1/health`
- **Method:** GET
- **Expected response:** HTTP 200, body contains `"status": "healthy"`
- **No auth required**

---

## Scaling Considerations (Future)

The current design is suited for a personal/home project on free-tier managed services. For scaling:

| Concern | Current approach | Scaled approach |
|---------|-----------------|-----------------|
| Multiple sensors | Supported via `sensor_id` | No change needed |
| Higher write throughput | Single uvicorn worker on Render | Scale up Render instance; or add multiple workers |
| HA MongoDB | MongoDB Atlas (cloud-managed) | Upgrade Atlas cluster tier |
| Persistent alerts | None (client-side only) | Add a notifications service (email, Pushover, etc.) |
