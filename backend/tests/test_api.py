import pytest
from bson import ObjectId
from datetime import datetime, timezone
from unittest.mock import MagicMock


VALID_PAYLOAD = {
    "sensor_id": "pomegranate-01",
    "temperature": 24.5,
    "humidity": 52.0,
    "soil_moisture": 38.0,
    "light_lux": 12500.0,
    "location": "living-room",
}


# ── POST /readings ─────────────────────────────────────────────────────────

class TestPostReading:
    def test_success_returns_201(self, client, auth_headers, mock_readings_col, mock_sensors_col):
        mock_readings_col.insert_one.return_value = MagicMock(
            inserted_id=ObjectId("507f1f77bcf86cd799439011")
        )
        resp = client.post("/api/v1/readings", json=VALID_PAYLOAD, headers=auth_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["sensor_id"] == "pomegranate-01"
        assert data["temperature"] == 24.5
        assert data["soil_moisture"] == 38.0
        assert "id" in data

    def test_missing_api_key_returns_401(self, client):
        resp = client.post("/api/v1/readings", json=VALID_PAYLOAD)
        assert resp.status_code == 401

    def test_wrong_api_key_returns_401(self, client):
        resp = client.post("/api/v1/readings", json=VALID_PAYLOAD,
                           headers={"X-API-Key": "wrong-key"})
        assert resp.status_code == 401

    def test_temperature_out_of_range_returns_422(self, client, auth_headers):
        bad = {**VALID_PAYLOAD, "temperature": 100.0}
        resp = client.post("/api/v1/readings", json=bad, headers=auth_headers)
        assert resp.status_code == 422

    def test_humidity_out_of_range_returns_422(self, client, auth_headers):
        bad = {**VALID_PAYLOAD, "humidity": -5.0}
        resp = client.post("/api/v1/readings", json=bad, headers=auth_headers)
        assert resp.status_code == 422

    def test_invalid_sensor_id_returns_422(self, client, auth_headers):
        bad = {**VALID_PAYLOAD, "sensor_id": "sensor@bad!"}
        resp = client.post("/api/v1/readings", json=bad, headers=auth_headers)
        assert resp.status_code == 422

    def test_missing_required_field_returns_422(self, client, auth_headers):
        bad = {k: v for k, v in VALID_PAYLOAD.items() if k != "temperature"}
        resp = client.post("/api/v1/readings", json=bad, headers=auth_headers)
        assert resp.status_code == 422


# ── GET /readings ──────────────────────────────────────────────────────────

class TestGetReadings:
    def test_returns_200_with_list(self, client, auth_headers,
                                   mock_readings_col, sample_reading_doc):
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = MagicMock(return_value=iter([sample_reading_doc]))
        mock_readings_col.find.return_value.sort.return_value.skip.return_value.limit.return_value = mock_cursor
        mock_readings_col.count_documents.return_value = 1

        resp = client.get("/api/v1/readings", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "readings" in data
        assert data["total"] == 1

    def test_no_auth_returns_200(self, client, mock_readings_col, sample_reading_doc):
        mock_cursor = MagicMock()
        mock_cursor.__iter__ = MagicMock(return_value=iter([sample_reading_doc]))
        mock_readings_col.find.return_value.sort.return_value.skip.return_value.limit.return_value = mock_cursor
        mock_readings_col.count_documents.return_value = 1
        resp = client.get("/api/v1/readings")
        assert resp.status_code == 200


# ── GET /readings/{sensor_id}/latest ──────────────────────────────────────

class TestGetLatest:
    def test_returns_latest_reading(self, client, auth_headers,
                                    mock_readings_col, sample_reading_doc):
        mock_readings_col.find_one.return_value = sample_reading_doc
        resp = client.get("/api/v1/readings/pomegranate-01/latest", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["sensor_id"] == "pomegranate-01"

    def test_unknown_sensor_returns_404(self, client, auth_headers, mock_readings_col):
        mock_readings_col.find_one.return_value = None
        resp = client.get("/api/v1/readings/ghost-sensor/latest", headers=auth_headers)
        assert resp.status_code == 404


# ── GET /health ────────────────────────────────────────────────────────────

class TestHealth:
    def test_health_check_returns_200(self, client):
        resp = client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"
        assert resp.json()["database"] == "connected"
