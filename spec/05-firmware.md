# Pomegranate Monitor — Firmware Specification

## Hardware

### Microcontroller

| Property       | Value                        |
|----------------|------------------------------|
| Board          | ESP32 (any variant with WiFi)|
| Framework      | Arduino (via Arduino IDE)    |
| Serial baud    | 115200                       |

### Sensors and Pin Assignments

| Sensor                        | Pin     | Signal Type  | Notes                                          |
|-------------------------------|---------|--------------|------------------------------------------------|
| DHT22 (air temp + humidity)   | GPIO 4  | Digital (1-wire) | Requires 10kΩ pull-up resistor on data line |
| Capacitive soil moisture      | GPIO 34 | Analog (ADC) | 12-bit ADC; pin 34 is input-only on ESP32      |
| LDR (light dependent resistor)| GPIO 35 | Analog (ADC) | Pin 35 is input-only on ESP32                  |

**Note:** The BH1750 digital I2C light sensor was originally planned but was destroyed. The LDR is a substitute; lux values are estimated, not calibrated.

### Libraries

| Library        | Version (approximate) | Purpose                          |
|----------------|-----------------------|----------------------------------|
| `DHT sensor library` (Adafruit) | ≥ 1.4   | DHT22 temperature/humidity       |
| `WiFi.h`       | Built-in ESP32 core   | WiFi connection management       |
| `HTTPClient.h` | Built-in ESP32 core   | HTTP POST to REST API            |

---

## Sensor Calibration

### Soil Moisture (GPIO 34)

The capacitive sensor outputs a raw 12-bit ADC value. The mapping is inverted (higher voltage = drier soil):

| Condition | Raw ADC Value |
|-----------|--------------|
| Dry (air) | 3200         |
| Wet (submerged) | 1200   |

**Calibration formula:**
```c
#define SOIL_DRY_VALUE  3200
#define SOIL_WET_VALUE  1200

float soil_moisture = map(raw, SOIL_DRY_VALUE, SOIL_WET_VALUE, 0, 100);
soil_moisture = constrain(soil_moisture, 0.0, 100.0);
```

### Light (GPIO 35)

The LDR outputs a raw 12-bit ADC value (0–4095). A simple linear map is used to produce an estimated lux value:

```c
float light_lux = (raw_ldr / 4095.0) * 100000.0;
```

This is an approximation. The relationship between ADC voltage and actual lux is nonlinear and depends on the specific LDR's resistance curve and the voltage divider configuration.

---

## Firmware Behavior

### Constants

```c
#define SENSOR_ID          "pomegranate-01"
#define LOCATION           "living-room"
#define DHT_PIN            4
#define SOIL_PIN           34
#define LDR_PIN            35
#define SOIL_DRY_VALUE     3200
#define SOIL_WET_VALUE     1200
#define POST_INTERVAL_MS   30000   // 30 seconds
#define READ_INTERVAL_MS   2000    //  2 seconds
```

### `setup()`

1. Initialize Serial at 115200.
2. Initialize DHT22 sensor object.
3. Connect to WiFi using `WIFI_SSID` and `WIFI_PASSWORD` from `secrets.h`. Block until connected.
4. Print IP address to Serial.

### `loop()`

Runs on a non-blocking timer pattern using `millis()`:

**Every 2 seconds:**
1. Read DHT22 → `temperature`, `humidity`.
2. If DHT22 returns NaN, retry once. If still NaN, skip the read and log an error.
3. Read ADC pin 34 → map to `soil_moisture` (0–100%).
4. Read ADC pin 35 → map to `light_lux` (0–100,000).
5. Print all four values to Serial.

**Every 30 seconds:**
1. Check WiFi status. If disconnected, attempt `WiFi.reconnect()` and return.
2. Build JSON string into a 256-byte `char` buffer using `snprintf`:
   ```json
   {"sensor_id":"pomegranate-01","temperature":XX.X,"humidity":XX.X,"soil_moisture":XX.X,"light_lux":XXXXX.X,"location":"living-room"}
   ```
   Note: No `timestamp` field is sent. The backend auto-fills `timestamp = UTC now`.
3. Create `HTTPClient` object, call `http.begin(API_URL)`.
4. Add header `X-API-Key: <API_KEY>` and `Content-Type: application/json`.
5. Call `http.POST(payload)`.
6. If response code == 201: log "Reading sent successfully".
7. If response code != 201: log error code + response body.
8. Call `http.end()`.

### Secrets File (`secrets.h`)

```c
// firmware/secrets.h — DO NOT COMMIT TO SOURCE CONTROL
#define WIFI_SSID     "YourNetworkName"
#define WIFI_PASSWORD "YourPassword"
#define API_KEY       "your-api-key-here"
#define API_URL       "http://<host-ip>:8000/api/v1/readings"
```

For a cloud deployment, `API_URL` should point to the public hostname with HTTPS, e.g.:
```c
#define API_URL "https://monitor.example.com/api/v1/readings"
```

HTTPS requires enabling the `WiFiClientSecure` class and loading the server's CA certificate or disabling certificate verification (insecure, only for testing).

---

## Known Issues

| Issue | Description |
|-------|-------------|
| No timestamp in payload | Firmware does not read RTC or NTP. The backend uses server receive time as the timestamp. If the backend is down when a reading is taken, that reading is lost — there is no local buffering. |
| LDR lux is estimated | The linear map produces plausible values but is not physically calibrated. Values should be treated as relative, not absolute lux. |
| `secrets.h` was committed | The file containing real WiFi credentials and API key was accidentally committed to the repository. If this repo is public, those credentials must be rotated. The file is now in `.gitignore`. |
| LAN-only URL | `API_URL` is a local network IP. For cloud deployment, this must be updated in `secrets.h` and the firmware reflashed. |

---

## Flashing Instructions

1. Install Arduino IDE ≥ 2.0.
2. Add ESP32 board package: Preferences → Additional Board Manager URLs → add the Espressif ESP32 URL.
3. Install "DHT sensor library" by Adafruit via Library Manager.
4. Copy `firmware/secrets.h.example` to `firmware/secrets.h` and fill in credentials.
5. Open `firmware/pomegranate_monitor.ino` in Arduino IDE.
6. Select board: "ESP32 Dev Module" (or your specific variant).
7. Select the correct COM port.
8. Click Upload.
9. Open Serial Monitor at 115200 baud to verify readings and POST responses.
