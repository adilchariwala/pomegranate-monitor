# Pomegranate Monitor — Use Cases

## Actors

| Actor       | Description |
|-------------|-------------|
| **ESP32**   | The microcontroller embedded with the plant. Reads sensors, sends data. |
| **Plant Owner** | The human who monitors the dashboard and cares for the plant. |
| **System**  | Background processes (auto-refresh, TTL purge, Docker restart). |

---

## UC-01: Ingest Sensor Reading

**Actor:** ESP32  
**Trigger:** Every 30 seconds (timer interrupt in firmware loop)  
**Precondition:** ESP32 is powered, WiFi is connected, and the API host is reachable.

**Main Flow:**
1. ESP32 reads DHT22 → temperature (°C) and humidity (%).
2. ESP32 reads capacitive soil sensor (ADC pin 34) → maps raw value (3200 dry → 1200 wet) to 0–100%.
3. ESP32 reads LDR (ADC pin 35) → maps raw value (0–4095) to estimated lux (0–100,000).
4. ESP32 builds a JSON payload with `sensor_id="pomegranate-01"`, `location="living-room"`, and the four readings.
5. ESP32 POSTs to `POST /api/v1/readings` with `X-API-Key` header.
6. Backend validates the payload via Pydantic.
7. Backend inserts a new document into the `readings` collection with `timestamp=UTC now`.
8. Backend upserts the sensor registry in the `sensors` collection (`last_seen` updated).
9. Backend returns HTTP 201 with the stored document.
10. ESP32 logs success to Serial.

**Alternate Flows:**
- **1a.** DHT22 returns NaN → ESP32 retries once; if still NaN, skips this POST cycle.
- **5a.** WiFi disconnected → ESP32 skips POST, attempts WiFi reconnect, continues reading loop.
- **6a.** Pydantic validation fails (value out of range, invalid sensor_id) → backend returns HTTP 422; ESP32 logs the error.
- **6b.** Wrong or missing `X-API-Key` → backend returns HTTP 401; ESP32 logs the error.

---

## UC-02: View Live Dashboard

**Actor:** Plant Owner  
**Trigger:** Plant owner opens the web app in a browser.  
**Precondition:** Docker stack is running; frontend is accessible on port 80.

**Main Flow:**
1. Browser loads the React app.
2. App checks `sessionStorage` for a saved API key.
3. **If no key stored:** Login screen is displayed. Plant owner enters the API key.
4. App calls `GET /api/v1/health` to validate the key is accepted.
5. On success, key is saved to `sessionStorage` and the dashboard loads.
6. App fetches: latest reading (`/readings/{sensor_id}/latest`), stats (`/sensors/{sensor_id}/stats`), history (`/readings` with time range), sensor list (`/sensors`).
7. Dashboard renders:
   - Four reading cards (temperature °F, humidity %, soil moisture %, light lux) with color-coded status.
   - Health panel (composite score 0–100, status label, alert messages).
   - Chart panel (line charts per metric over selected time window).
   - Live/offline status dot (green if last reading < 2 minutes ago).
8. Dashboard auto-refreshes all data every 30 seconds.

**Alternate Flows:**
- **3a.** Wrong API key → app shows "Authentication failed" message; key is not saved.
- **6a.** Network error or backend down → app shows error state on affected panels.
- **7a.** No readings exist for the selected sensor → empty/null state is shown in cards and chart.

---

## UC-03: Switch Sensor or Time Window

**Actor:** Plant Owner  
**Trigger:** Plant owner selects a different sensor from the dropdown or clicks a time window tab.

**Main Flow:**
1. Plant owner selects a sensor ID from the dropdown (populated from `GET /api/v1/sensors`).
2. Plant owner selects a time window: 6h, 24h, 48h, or 7d.
3. App re-fetches latest, stats, and history for the selected sensor and window.
4. All panels update to reflect the new selection.

---

## UC-04: Receive Plant Health Alert

**Actor:** Plant Owner  
**Trigger:** Dashboard renders and a sensor reading is outside acceptable thresholds.

**Main Flow:**
1. `HealthPanel` evaluates the latest reading against alert thresholds (see Data Models spec).
2. Alert messages are displayed in a scrollable list (e.g., "Soil moisture is critically low (12%)").
3. The health score gauge and status label reflect the composite score.
4. Reading cards are color-coded: green = good, yellow = warning, red = alert.

**Note:** Alerts are derived client-side from the latest reading. There is no push notification or email alert system.

---

## UC-05: Automatic Data Expiry

**Actor:** System (MongoDB TTL)  
**Trigger:** MongoDB TTL background job (runs every ~60 seconds).

**Main Flow:**
1. MongoDB checks the `timestamp` field on all documents in the `readings` collection.
2. Documents where `timestamp` is older than 30 days (`expireAfterSeconds=2592000`) are automatically deleted.
3. No action required from any other actor.

**Note:** The `sensors` collection is not subject to TTL; sensor registry entries persist indefinitely.

---

## UC-06: Restart After Outage

**Actor:** System (Docker)  
**Trigger:** Host machine reboots or any Docker service crashes.

**Main Flow:**
1. Docker restarts all services (`restart: unless-stopped`).
2. `mongo` starts first; `backend` waits for `mongo` to be reachable.
3. `backend` reconnects to MongoDB, verifies indexes exist.
4. `frontend` resumes serving the React app.
5. ESP32 (independently) reconnects WiFi and resumes POSTing after the next 30-second interval.

---

## UC-07: Add a New Sensor

**Actor:** Plant Owner (advanced)  
**Trigger:** A second ESP32 is set up with a different `sensor_id`.

**Main Flow:**
1. New firmware is flashed with `SENSOR_ID` set to a new unique value (e.g., `"pomegranate-02"`).
2. Firmware POSTs readings to the same API endpoint.
3. Backend auto-registers the new sensor in the `sensors` collection on first POST.
4. Plant owner opens the dashboard and selects the new sensor from the dropdown.
5. All panels display data for the selected sensor.

**No backend configuration change is required to add a sensor.**
