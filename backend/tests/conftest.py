import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from datetime import datetime, timezone

TEST_API_KEY = "test-key-abc123"


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    monkeypatch.setenv("MONGODB_URL", "mongodb://localhost:27017")
    monkeypatch.setenv("API_KEY", TEST_API_KEY)
    monkeypatch.setenv("DATABASE_NAME", "test_db")


@pytest.fixture
def mock_readings_col():
    return MagicMock()


@pytest.fixture
def mock_sensors_col():
    return MagicMock()


@pytest.fixture
def client(mock_readings_col, mock_sensors_col):
    from app.main import app
    with patch("app.main.get_readings_collection", return_value=mock_readings_col), \
         patch("app.main.get_sensors_collection", return_value=mock_sensors_col), \
         patch("app.main.ping_db", return_value=True):
        with TestClient(app) as c:
            yield c


@pytest.fixture
def auth_headers():
    return {"X-API-Key": TEST_API_KEY}


@pytest.fixture
def sample_reading_doc():
    from bson import ObjectId
    return {
        "_id": ObjectId("507f1f77bcf86cd799439011"),
        "sensor_id": "pomegranate-01",
        "temperature": 24.5,
        "humidity": 52.0,
        "soil_moisture": 38.0,
        "light_lux": 12500.0,
        "timestamp": datetime(2024, 3, 15, 14, 30, 0, tzinfo=timezone.utc),
        "location": "living-room",
    }
