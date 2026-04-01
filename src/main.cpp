// some test code for dht22
#include <Arduino.h>
#include <DHT.h>

#define DHTPIN 4
#define DHTTYPE DHT22

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200);
  dht.begin();
  delay(1000);
  Serial.println("DHT22 live readings:");
}

void loop() {
  float humidity = dht.readHumidity();
  float tempC = dht.readTemperature();

  if (isnan(humidity) || isnan(tempC)) {
    Serial.println("Failed to read from DHT22");
  } else {
    Serial.print("Temp: ");
    Serial.print(tempC);
    Serial.print(" C, Humidity: ");
    Serial.print(humidity);
    Serial.println(" %");
  }

  delay(2000);
}