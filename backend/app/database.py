from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.collection import Collection
from app.config import settings

_client: MongoClient | None = None


def get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(settings.mongodb_url)
    return _client


def get_db():
    return get_client()[settings.database_name]


def get_readings_collection() -> Collection:
    db = get_db()
    col = db["readings"]
    # Compound index: fast range queries per sensor
    col.create_index([("sensor_id", ASCENDING), ("timestamp", DESCENDING)])
    # TTL index: auto-delete readings older than 30 days
    col.create_index([("timestamp", ASCENDING)], expireAfterSeconds=2592000)
    return col


def get_sensors_collection() -> Collection:
    db = get_db()
    col = db["sensors"]
    col.create_index([("last_seen", DESCENDING)])
    return col


def ping_db() -> bool:
    try:
        get_client().admin.command("ping")
        return True
    except Exception:
        return False
