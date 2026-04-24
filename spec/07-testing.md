# Pomegranate Monitor — Testing Specification

## Overview

Testing covers the backend only. There are no automated tests for the firmware or frontend.

**Test runner:** pytest 8.3.2  
**Async support:** pytest-asyncio 0.23.8  
**HTTP test client:** FastAPI `TestClient` (wraps HTTPX)  
**Mocking:** `unittest.mock.MagicMock` and `monkeypatch`

**Run tests:**
```bash
cd backend
pip install -r requirements.txt
pytest tests/ -v
```

---

## Test Configuration (`tests/conftest.py`)

### Environment setup

Before any test, `monkeypatch` sets the required environment variables so `pydantic-settings` can initialize:

```python
os.environ["MONGODB_URL"] = "mongodb://localhost:27017"
os.environ["API_KEY"]     = "test-api-key"
```

### Mocked MongoDB layer

All database interactions are mocked using `MagicMock`. Three functions are monkeypatched on the `app.database` module:

| Patched function          | What it returns |
|---------------------------|-----------------|
| `get_readings_collection` | `MagicMock` representing the `readings` collection |
| `get_sensors_collection`  | `MagicMock` representing the `sensors` collection |
| `ping_db`                 | `MagicMock` (no-op, does not raise) |

This means all tests run without a real MongoDB instance.

### Fixtures

| Fixture           | Scope   | Description |
|-------------------|---------|-------------|
| `client`          | function | `TestClient(app)` — the FastAPI test client |
| `auth_headers`    | function | `{"X-API-Key": "test-api-key"}` |
| `sample_reading_doc` | function | A dict representing a MongoDB document with all fields, including `_id` as `ObjectId` |

**`sample_reading_doc`:**
```python
{
    "_id":           ObjectId("507f1f77bcf86cd799439011"),
    "sensor_id":     "test-sensor",
    "temperature":   25.0,
    "humidity":      55.0,
    "soil_moisture": 45.0,
    "light_lux":     5000.0,
    "timestamp":     datetime(2024, 1, 1, 12, 0, 0),
    "location":      "test-location"
}
```

---

## Test Suite: `tests/test_api.py`

Integration-style tests that call the FastAPI routes through `TestClient`.

### `TestPostReading` — 7 tests

| Test | Input | Expected outcome |
|------|-------|-----------------|
| `test_post_reading_success` | Valid payload, correct API key | HTTP 201; response contains all fields; `insert_one` called once; `update_one` called once (sensor upsert) |
| `test_post_reading_missing_auth` | Valid payload, no `X-API-Key` header | HTTP 401 |
| `test_post_reading_wrong_auth` | Valid payload, wrong API key | HTTP 401 |
| `test_post_reading_invalid_temperature` | `temperature: 200.0` (above 85.0) | HTTP 422 |
| `test_post_reading_negative_humidity` | `humidity: -5.0` | HTTP 422 |
| `test_post_reading_invalid_sensor_id` | `sensor_id: "invalid id!"` (contains space + `!`) | HTTP 422 |
| `test_post_reading_missing_field` | Payload omits `soil_moisture` | HTTP 422 |

### `TestGetReadings` — 2 tests

| Test | Setup | Expected outcome |
|------|-------|-----------------|
| `test_get_readings_success` | Mock cursor returns `[sample_reading_doc]` | HTTP 200; array with one item; fields correctly serialized |
| `test_get_readings_no_auth` | No `X-API-Key` header | HTTP 401 |

### `TestGetLatest` — 2 tests

| Test | Setup | Expected outcome |
|------|-------|-----------------|
| `test_get_latest_success` | `find_one` returns `sample_reading_doc` | HTTP 200; single reading object |
| `test_get_latest_not_found` | `find_one` returns `None` | HTTP 404 |

### `TestHealth` — 1 test

| Test | Setup | Expected outcome |
|------|-------|-----------------|
| `test_health_check` | `ping_db` mock does not raise | HTTP 200; `status=="healthy"`, `database=="connected"` |

---

## Test Suite: `tests/test_models.py`

Unit tests for Pydantic validation and the health score algorithm. No HTTP calls; no mocking needed.

### `TestSensorReadingValidation` — 9 tests

| Test | What is validated |
|------|-------------------|
| `test_valid_reading` | All fields in range → model instantiates successfully |
| `test_temperature_too_high` | `temperature=100.0` → `ValidationError` raised |
| `test_temperature_too_low` | `temperature=-50.0` → `ValidationError` raised |
| `test_humidity_out_of_range` | `humidity=110.0` → `ValidationError` raised |
| `test_soil_moisture_negative` | `soil_moisture=-1.0` → `ValidationError` raised |
| `test_light_lux_too_high` | `light_lux=250000.0` → `ValidationError` raised |
| `test_auto_timestamp` | No `timestamp` provided → `timestamp` is set to a datetime close to `now()` |
| `test_optional_location` | `location` omitted → model instantiates; `location is None` |
| `test_invalid_sensor_id` | `sensor_id="bad id!"` → `ValidationError` raised |

### `TestHealthScore` — 5 tests

| Test | Input | Expected result |
|------|-------|-----------------|
| `test_perfect_conditions` | temp=25, hum=50, soil=45, light=15000 | score == 100.0 |
| `test_low_soil_moisture` | soil=10 (well below 30%) → penalty applied | score < 100 and score > 0 |
| `test_high_temperature` | temp=40 (above 35°C) → penalty applied | score < 100 |
| `test_zero_light` | light=0 → light sub-score=0 | score < 100 |
| `test_score_clamped_to_zero` | All values at worst possible extremes | score == 0.0 |

---

## Coverage Gaps

The following are not currently covered by automated tests:

| Area | Gap |
|------|-----|
| `GET /sensors` | No test exists |
| `GET /sensors/{id}/stats` | No test exists |
| `GET /readings` query params | Only the basic 200/401 case is tested; filters (`sensor_id`, `start`, `end`, `limit`, `offset`) are untested |
| `compute_health_score` edge cases | Low humidity, high humidity, and boundary conditions at exactly 18°C / 35°C are untested |
| Frontend | No automated tests |
| Firmware | No automated tests |

---

## Adding New Tests

To add a test for a new API endpoint:

1. Add a new class in `test_api.py` (e.g., `TestGetSensors`).
2. In `setUp` or within the test, configure the mock collection's return value:
   ```python
   mock_sensors_col = get_sensors_collection.return_value
   mock_sensors_col.find.return_value = [...]
   ```
3. Call `self.client.get("/api/v1/sensors", headers=self.auth_headers)`.
4. Assert the status code and response body.
