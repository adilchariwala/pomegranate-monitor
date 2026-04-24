# Pomegranate Monitor — Specification Index

This directory contains the complete technical specification for the Pomegranate Monitor IoT plant health monitoring system. A developer (or AI coding tool) reading these files should be able to reproduce the entire working project from scratch.

## Files

| File | Contents |
|------|----------|
| [01-overview.md](01-overview.md) | System purpose, architecture diagram, service topology, repository layout, key design decisions |
| [02-use-cases.md](02-use-cases.md) | All use cases: sensor ingestion, live dashboard, sensor switching, health alerts, data expiry, outage recovery, multi-sensor |
| [03-data-models.md](03-data-models.md) | MongoDB collection schemas, indexes, Pydantic models, health score algorithm, alert thresholds |
| [04-api.md](04-api.md) | Complete REST API spec: all endpoints, request/response schemas, auth, error formats |
| [05-firmware.md](05-firmware.md) | ESP32 hardware, sensor pins, calibration formulas, firmware behavior, secrets file, flashing instructions |
| [06-frontend.md](06-frontend.md) | React component tree, state management, API client, chart and card specifications, nginx config |
| [07-testing.md](07-testing.md) | pytest setup, fixtures, mocking strategy, all test cases with inputs and expected outputs, coverage gaps |
| [08-deployment.md](08-deployment.md) | Docker Compose services, Dockerfiles, local and cloud deployment steps, TLS options, env vars, backup |

## Quick Start (Reproduction)

To build the project from these specs:

1. Read [01-overview.md](01-overview.md) for architecture and repo structure.
2. Read [03-data-models.md](03-data-models.md) and [04-api.md](04-api.md) to implement the backend.
3. Read [06-frontend.md](06-frontend.md) to implement the React dashboard.
4. Read [05-firmware.md](05-firmware.md) to write the ESP32 sketch.
5. Read [07-testing.md](07-testing.md) to write the test suite.
6. Read [08-deployment.md](08-deployment.md) to wire it all together with Docker Compose.

## System Summary

- **Hardware:** ESP32 with DHT22 (temp/humidity), capacitive soil sensor, LDR (light estimate)
- **Firmware:** Arduino C++; POSTs JSON to REST API every 30 seconds
- **Backend:** FastAPI + pymongo; API-key auth; stores readings in MongoDB with 30-day TTL
- **Database:** MongoDB Atlas (cloud-hosted); two collections (`readings`, `sensors`)
- **Frontend:** React 18 + Recharts; live cards, health score, time-series charts
- **Deployment (production):** MongoDB Atlas + Render Web Service (backend) + Render Static Site (frontend)
- **Deployment (local dev):** Docker Compose (3 services: mongo, backend, frontend)
