from datetime import datetime, timezone, timedelta
from typing import Optional

from fastapi import FastAPI, HTTPException, Security, Query
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from bson import ObjectId

from app.config import settings
from app.database import (
    get_readings_collection,
    get_sensors_collection,
    ping_db,
)
from app.models import (
    SensorReadingCreate,
    SensorReadingResponse,
    SensorResponse,
    StatsResponse,
    StatValues,
    HealthCheckResponse,
    doc_to_reading,
    compute_health_score,
)

# ── App setup ──────────────────────────────────────────────────────────────

app = FastAPI(
    title="Pomegranate Monitor API",
    description="IoT sensor data pipeline for pomegranate plant health monitoring",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth ───────────────────────────────────────────────────────────────────

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def require_api_key(key: str = Security(api_key_header)):
    if key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return key


# ── Health ─────────────────────────────────────────────────────────────────

@app.get("/api/v1/health", response_model=HealthCheckResponse, tags=["system"])
def health_check():
    ok = ping_db()
    return HealthCheckResponse(
        status="healthy" if ok else "unhealthy",
        database="connected" if ok else "disconnected",
        timestamp=datetime.now(timezone.utc),
    )


# ── POST /readings ─────────────────────────────────────────────────────────

@app.post("/api/v1/readings", response_model=SensorReadingResponse,
          status_code=201, tags=["readings"])
def post_reading(
    body: SensorReadingCreate,
    _key: str = Security(require_api_key),
):
    readings = get_readings_collection()
    sensors = get_sensors_collection()
    now = datetime.now(timezone.utc)

    doc = body.model_dump()
    if doc["timestamp"] is None:
        doc["timestamp"] = now

    result = readings.insert_one(doc)

    # Upsert sensor record
    sensors.update_one(
        {"_id": body.sensor_id},
        {
            "$setOnInsert": {"registered_at": now, "location": body.location},
            "$set": {"last_seen": now},
        },
        upsert=True,
    )

    doc["_id"] = result.inserted_id
    return doc_to_reading(doc)


# ── GET /readings ──────────────────────────────────────────────────────────

@app.get("/api/v1/readings", tags=["readings"])
def get_readings(
    sensor_id: Optional[str] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    bucket_minutes: Optional[int] = Query(None, ge=1, le=60),
    _key: str = Security(require_api_key),
):
    readings = get_readings_collection()
    query: dict = {}
    if sensor_id:
        query["sensor_id"] = sensor_id
    if start or end:
        query["timestamp"] = {}
        if start:
            query["timestamp"]["$gte"] = start
        if end:
            query["timestamp"]["$lte"] = end

    if bucket_minutes:
        bucket_ms = bucket_minutes * 60 * 1000
        pipeline = [
            {"$match": query},
            {"$addFields": {
                "bucket": {
                    "$toDate": {
                        "$multiply": [
                            {"$floor": {"$divide": [{"$toLong": "$timestamp"}, bucket_ms]}},
                            bucket_ms,
                        ]
                    }
                }
            }},
            {"$group": {
                "_id": "$bucket",
                "timestamp": {"$first": "$bucket"},
                "sensor_id": {"$first": "$sensor_id"},
                "temperature": {"$avg": "$temperature"},
                "humidity": {"$avg": "$humidity"},
                "soil_moisture": {"$avg": "$soil_moisture"},
                "light_lux": {"$avg": "$light_lux"},
                "location": {"$first": "$location"},
            }},
            {"$sort": {"timestamp": 1}},
        ]
        docs = list(readings.aggregate(pipeline))
        return {
            "count": len(docs),
            "total": len(docs),
            "readings": [doc_to_reading(d) for d in docs],
        }

    total = readings.count_documents(query)
    # Sort ascending so oldest data is returned first within the time window
    sort_dir = 1 if start else -1
    cursor = (
        readings.find(query)
        .sort("timestamp", sort_dir)
        .skip(offset)
        .limit(limit)
    )
    return {
        "count": min(limit, total - offset),
        "total": total,
        "readings": [doc_to_reading(d) for d in cursor],
    }


# ── GET /readings/{sensor_id}/latest ──────────────────────────────────────

@app.get("/api/v1/readings/{sensor_id}/latest",
         response_model=SensorReadingResponse, tags=["readings"])
def get_latest(
    sensor_id: str,
):
    readings = get_readings_collection()
    doc = readings.find_one(
        {"sensor_id": sensor_id},
        sort=[("timestamp", -1)],
    )
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"No readings found for sensor '{sensor_id}'",
        )
    return doc_to_reading(doc)


# ── GET /sensors ───────────────────────────────────────────────────────────

@app.get("/api/v1/sensors", tags=["sensors"])
def list_sensors():
    sensors = get_sensors_collection()
    docs = list(sensors.find().sort("last_seen", -1))
    return {
        "count": len(docs),
        "sensors": [
            SensorResponse(
                sensor_id=d["_id"],
                location=d.get("location"),
                registered_at=d["registered_at"],
                last_seen=d["last_seen"],
            )
            for d in docs
        ],
    }


# ── GET /sensors/{sensor_id}/stats ────────────────────────────────────────

@app.get("/api/v1/sensors/{sensor_id}/stats",
         response_model=StatsResponse, tags=["sensors"])
def get_stats(
    sensor_id: str,
    hours: int = Query(24, ge=1, le=720),
):
    readings = get_readings_collection()
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    pipeline = [
        {"$match": {"sensor_id": sensor_id, "timestamp": {"$gte": since}}},
        {
            "$group": {
                "_id": None,
                "temp_min": {"$min": "$temperature"},
                "temp_max": {"$max": "$temperature"},
                "temp_avg": {"$avg": "$temperature"},
                "hum_min": {"$min": "$humidity"},
                "hum_max": {"$max": "$humidity"},
                "hum_avg": {"$avg": "$humidity"},
                "soil_min": {"$min": "$soil_moisture"},
                "soil_max": {"$max": "$soil_moisture"},
                "soil_avg": {"$avg": "$soil_moisture"},
                "lux_min": {"$min": "$light_lux"},
                "lux_max": {"$max": "$light_lux"},
                "lux_avg": {"$avg": "$light_lux"},
                "count": {"$sum": 1},
            }
        },
    ]

    results = list(readings.aggregate(pipeline))
    if not results:
        raise HTTPException(
            status_code=404,
            detail=f"No readings for sensor '{sensor_id}' in the last {hours} hours",
        )

    r = results[0]
    health = compute_health_score(
        r["temp_avg"], r["hum_avg"], r["soil_avg"], r["lux_avg"]
    )

    return StatsResponse(
        sensor_id=sensor_id,
        period_hours=hours,
        temperature=StatValues(min=r["temp_min"], max=r["temp_max"], avg=round(r["temp_avg"], 2)),
        humidity=StatValues(min=r["hum_min"], max=r["hum_max"], avg=round(r["hum_avg"], 2)),
        soil_moisture=StatValues(min=r["soil_min"], max=r["soil_max"], avg=round(r["soil_avg"], 2)),
        light_lux=StatValues(min=r["lux_min"], max=r["lux_max"], avg=round(r["lux_avg"], 1)),
        reading_count=r["count"],
        health_score=health,
    )
