import pytest
from pydantic import ValidationError
from app.models import SensorReadingCreate, compute_health_score


class TestSensorReadingCreate:
    def _valid(self, **overrides):
        data = {
            "sensor_id": "pomegranate-01",
            "temperature": 24.5,
            "humidity": 52.0,
            "soil_moisture": 38.0,
            "light_lux": 12500.0,
            "location": "living-room",
        }
        data.update(overrides)
        return data

    def test_valid_payload_parses(self):
        r = SensorReadingCreate(**self._valid())
        assert r.sensor_id == "pomegranate-01"
        assert r.timestamp is not None  # auto-filled

    def test_temperature_too_high(self):
        with pytest.raises(ValidationError):
            SensorReadingCreate(**self._valid(temperature=90.0))

    def test_temperature_too_low(self):
        with pytest.raises(ValidationError):
            SensorReadingCreate(**self._valid(temperature=-50.0))

    def test_humidity_above_100(self):
        with pytest.raises(ValidationError):
            SensorReadingCreate(**self._valid(humidity=101.0))

    def test_humidity_negative(self):
        with pytest.raises(ValidationError):
            SensorReadingCreate(**self._valid(humidity=-1.0))

    def test_soil_moisture_out_of_range(self):
        with pytest.raises(ValidationError):
            SensorReadingCreate(**self._valid(soil_moisture=150.0))

    def test_light_lux_negative(self):
        with pytest.raises(ValidationError):
            SensorReadingCreate(**self._valid(light_lux=-10.0))

    def test_invalid_sensor_id_special_chars(self):
        with pytest.raises(ValidationError):
            SensorReadingCreate(**self._valid(sensor_id="bad@sensor!"))

    def test_valid_sensor_id_with_hyphens(self):
        r = SensorReadingCreate(**self._valid(sensor_id="sensor-abc-01"))
        assert r.sensor_id == "sensor-abc-01"

    def test_optional_location(self):
        r = SensorReadingCreate(**self._valid(location=None))
        assert r.location is None


class TestHealthScore:
    def test_perfect_conditions(self):
        score = compute_health_score(
            temp_avg=25.0, humidity_avg=50.0, soil_avg=45.0, lux_avg=15000.0
        )
        assert score == 100.0

    def test_cold_temp_reduces_score(self):
        score = compute_health_score(
            temp_avg=5.0, humidity_avg=50.0, soil_avg=45.0, lux_avg=15000.0
        )
        assert score < 80.0

    def test_zero_light_reduces_score(self):
        score = compute_health_score(
            temp_avg=25.0, humidity_avg=50.0, soil_avg=45.0, lux_avg=0.0
        )
        assert score < 80.0

    def test_dry_soil_reduces_score(self):
        score = compute_health_score(
            temp_avg=25.0, humidity_avg=50.0, soil_avg=5.0, lux_avg=15000.0
        )
        assert score < 90.0

    def test_score_bounded_0_to_100(self):
        score = compute_health_score(
            temp_avg=-100.0, humidity_avg=100.0, soil_avg=0.0, lux_avg=0.0
        )
        assert 0.0 <= score <= 100.0
