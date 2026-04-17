#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>
#include "secrets.h"

// ── Pin Definitions ────────────────────────────────────────────────────────
#define DHT_PIN        4
#define DHT_TYPE       DHT22
#define SOIL_PIN       34
#define LDR_PIN        35

// soil sensor calibration
#define SOIL_DRY       3200
#define SOIL_WET       1200

// ── Config ─────────────────────────────────────────────────────────────────
#define POST_INTERVAL_MS  30000
#define SENSOR_ID         "pomegranate-01"
#define LOCATION          "living-room"

DHT dht(DHT_PIN, DHT_TYPE);

// ── WiFi ───────────────────────────────────────────────────────────────────
void connectWiFi() {
  Serial.print("[WiFi] Connecting to ");
  Serial.print(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("\n[WiFi] Connected — IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\n[WiFi] Failed to connect. Will retry.");
  }
}

// ── Soil moisture → 0–100% ─────────────────────────────────────────────────
float readSoilMoisture() {
  int raw = analogRead(SOIL_PIN);
  raw = constrain(raw, SOIL_WET, SOIL_DRY);
  return map(raw, SOIL_DRY, SOIL_WET, 0, 100);
}

// ── Light → lux estimate ───────────────────────────────────────────────────
float readLux() {
  int raw = analogRead(LDR_PIN);
  return map(raw, 0, 4095, 0, 100000);
}

// ── POST to API ─────────────────────────────────────────────────────────────
bool postReading(float temp, float humidity, float soil, float lux) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[HTTP] Not connected, skipping POST.");
    return false;
  }

  HTTPClient http;
  http.begin(API_URL);
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);

  char body[256];
  snprintf(body, sizeof(body),
    "{\"sensor_id\":\"%s\","
    "\"temperature\":%.2f,"
    "\"humidity\":%.2f,"
    "\"soil_moisture\":%.2f,"
    "\"light_lux\":%.1f,"
    "\"location\":\"%s\"}",
    SENSOR_ID, temp, humidity, soil, lux, LOCATION);

  Serial.print("[HTTP] POST → ");
  Serial.println(API_URL);
  Serial.print("[HTTP] Body: ");
  Serial.println(body);

  int code = http.POST(body);

  if (code == 201) {
    Serial.println("[HTTP] ✓ Reading stored.");
    http.end();
    return true;
  } else {
    Serial.print("[HTTP] Error ");
    Serial.print(code);
    Serial.print(": ");
    Serial.println(http.getString());
    http.end();
    return false;
  }
}

// ── Setup ───────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n[Boot] Pomegranate Monitor starting...");

  dht.begin();
  connectWiFi();
  Serial.println("[Boot] Ready.");
}

// ── Loop ────────────────────────────────────────────────────────────────────
void loop() {
  static unsigned long lastPost = 0;
  unsigned long now = millis();

  float temp     = dht.readTemperature();
  float humidity = dht.readHumidity();
  float soil     = readSoilMoisture();
  float lux      = readLux();

  Serial.print("Raw soil: ");
  Serial.println(analogRead(SOIL_PIN));

  if (isnan(temp) || isnan(humidity)) {
    Serial.println("[Sensor] DHT22 read failed, retrying...");
    delay(2000);
    return;
  }

  Serial.print("[Sensor] Temp: ");
  Serial.print(temp);
  Serial.print("°C | Humidity: ");
  Serial.print(humidity);
  Serial.print("% | Soil: ");
  Serial.print(soil);
  Serial.print("% | Light: ");
  Serial.print(lux);
  Serial.println(" lux");

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[WiFi] Reconnecting...");
    connectWiFi();
  }

  if (now - lastPost >= POST_INTERVAL_MS) {
    if (postReading(temp, humidity, soil, lux)) {
      lastPost = now;
    }
  }

  delay(2000);
}