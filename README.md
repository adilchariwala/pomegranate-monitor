## 🌱 Pomegranate Monitor 

---


##  Current Status 
- Sensor-to-database pipeline is working. Data is transmitted through a well-defined API protocol with error detection and handling.
- Unit testing has thoroughly error-checked the transmission process.
- DHT22 and Soil Sensor are transmitting, BH1750 is not. Switched over to a LDR, BH1750 is cooked. 



##  Week 10 Status

At this stage of development:

- ESP32 firmware successfully built and deployed using PlatformIO  
- DHT22 sensor connected and collecting live temperature and humidity data local Data output is structured for future API integration  


---

## 🔧 Current Functionality

The system currently:

- Reads **air temperature (°C)** and **relative humidity (%)** from the DHT22  
- Outputs live data every 2 seconds via the serial monitor  
- Includes basic error handling for failed sensor reads  


 
### What Data Will Be Collected
 
This project collects the following environmental readings from around and inside the soil of a pomegranate plant:
 
| Sensor | Measurement | Why It Matters for Pomegranates |
|--------|-------------|----------------------------------|
| DHT22 | Air temperature (°C) | Pomegranates thrive between 18–35°C; frost can kill them |
| DHT22 | Relative humidity (%) | High humidity increases disease risk |
| Capacitive soil moisture sensor | Soil moisture (%) | Pomegranates prefer dry-between-watering cycles |
| BH1750 | Light intensity (lux) | Pomegranates need full sun — 6+ hours above 10,000 lux per day |

### Hardware
 Component | Purpose |
|-----------|---------|
| ESP32  board | Microcontroller with built-in WiFi |
| DHT22 | Air temperature + humidity 
| Capacitive soil moisture sensor | Soil wetness |
| BH1750 | Accurate light intensity in lux |




### What the End User Will See on the Dashboard
 
- **Live readings** — current soil moisture, air temperature, humidity, and light level in lux
- **Time-series charts** — each metric plotted over the past 24 hours, 7 days, or 30 days
- **Watering history** — automatically logged each time moisture drops below threshold and recovers
- **Daily light summary** — total hours above 10,000 lux per day so the plant's sun exposure is trackable over weeks
- **Plant health score** — a simple composite score (0–100) combining all four metrics
- **Alerts panel** — warnings when soil is too dry, temperature is out of range, or light has been consistently low
 
---
 