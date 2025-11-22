# Quickstart: UserInfo Report

**Feature**: UserInfo Report  
**Date**: 2025-11-22  
**Purpose**: Get started with UserInfo Report feature development

## Overview

The UserInfo Report feature enables comprehensive user telemetry collection, ad interaction tracking, time-based analytics, and reporting capabilities. This quickstart guide helps developers understand the architecture and get started with implementation.

## Architecture Overview

### Components

1. **Telemetry Collection Service** (`backend/app/services/telemetry.py`)
   - Captures user sessions, device information, location data
   - Enriches data with IP geolocation

2. **Interaction Tracking Service** (`backend/app/services/interactions.py`)
   - Logs all ad interaction events (impressions, clicks, completions, etc.)
   - Implements append-only event logging pattern

3. **Analytics Service** (`backend/app/services/analytics.py`)
   - Computes time-based aggregations (hourly heatmaps, daily trends)
   - Maintains materialized views for performance

4. **Reporting Service** (`backend/app/services/reporting.py`)
   - Generates user information reports
   - Provides aggregate reports with filtering

5. **Risk Scoring Service** (`backend/app/services/risk_scoring.py`)
   - Computes real-time risk scores for fraud detection
   - Implements progressive response tiers

### Data Flow

```
Client → API Endpoint → Service Layer → Database
                              ↓
                    Background Tasks (ETL, Aggregations)
```

## Database Setup

### 1. Create Migrations

```bash
# From backend directory
docker compose exec backend bash
alembic revision --autogenerate -m "add_userinfo_report_models"
alembic upgrade head
```

### 2. Verify Tables

```sql
-- Check new tables exist
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name LIKE '%user%' OR table_name LIKE '%interaction%';
```

## API Endpoints

### Telemetry Collection

**Create Session**
```bash
POST /api/v1/telemetry/session
Content-Type: application/json

{
  "openid": "user_12345",
  "nickname": "John Doe",
  "ip_address": "192.168.1.1",
  "device_snapshot": {
    "os_family": "iOS",
    "os_version": "17.0",
    "device_class": "mobile",
    "screen_resolution": "375x667",
    "screen_density": 326.0,
    "viewport_width": 375,
    "viewport_height": 667
  }
}
```

**Update Session End**
```bash
PATCH /api/v1/telemetry/session/{session_id}
Content-Type: application/json

{
  "end_timestamp": "2025-11-22T10:30:00Z"
}
```

### Ad Interaction Tracking

**Log Interaction**
```bash
POST /api/v1/interactions
Content-Type: application/json

{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "session_id": "660e8400-e29b-41d4-a716-446655440001",
  "ad_type": "reward",
  "ad_creative_id": "ad_123",
  "action": "impression",
  "timestamp": "2025-11-22T10:00:00Z",
  "device_snapshot": { ... },
  "location_snapshot": { ... }
}
```

### Analytics

**Get Hourly Heatmap**
```bash
GET /api/v1/analytics/hourly?date=2025-11-22&days=7
```

**Get Daily Trends**
```bash
GET /api/v1/analytics/daily?start_date=2025-11-15&end_date=2025-11-22
```

**Get User Activity Patterns**
```bash
GET /api/v1/analytics/user/{user_id}/patterns
```

### Reports

**Get User Report**
```bash
GET /api/v1/reports/user/{user_id}
```

**Get Aggregate Reports**
```bash
GET /api/v1/reports/aggregate?device_type=mobile&country=US&start_date=2025-11-15
```

**Export Report**
```bash
POST /api/v1/reports/export
Content-Type: application/json

{
  "format": "CSV",
  "report_type": "user",
  "filters": { "user_id": "..." },
  "date_range": {
    "start_date": "2025-11-15",
    "end_date": "2025-11-22"
  }
}
```

## Development Workflow

### 1. Add New Model

```python
# backend/app/models.py
from sqlmodel import Field, SQLModel

class UserProfile(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    openid: str = Field(unique=True, index=True)
    # ... other fields
```

### 2. Create Migration

```bash
alembic revision --autogenerate -m "add_user_profile"
alembic upgrade head
```

### 3. Add CRUD Operations

```python
# backend/app/crud.py
def create_user_profile(session: Session, user_profile: UserProfileCreate) -> UserProfile:
    db_user = UserProfile(**user_profile.dict())
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user
```

### 4. Create API Route

```python
# backend/app/api/routes/userinfo.py
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user

router = APIRouter()

@router.post("/telemetry/session", response_model=SessionResponse)
def create_session(
    session_data: SessionCreate,
    current_user: User = Depends(get_current_user)
):
    # Implementation
    pass
```

### 5. Register Route

```python
# backend/app/api/main.py
from app.api.routes import userinfo

api_router.include_router(
    userinfo.router,
    prefix="/telemetry",
    tags=["Telemetry"]
)
```

### 6. Regenerate Frontend Client

```bash
./scripts/generate-client.sh
```

## Background Tasks

### Setup Celery (if not already configured)

```python
# backend/app/core/celery_app.py
from celery import Celery

celery_app = Celery("app")
celery_app.conf.broker_url = "redis://localhost:6379/0"
celery_app.conf.result_backend = "redis://localhost:6379/0"
```

### Create ETL Task

```python
# backend/app/services/analytics.py
from app.core.celery_app import celery_app

@celery_app.task
def aggregate_daily_metrics(date: str):
    # Compute daily metrics for all users
    pass
```

### Schedule Tasks

```python
# backend/app/core/celery_app.py
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    "aggregate-daily-metrics": {
        "task": "app.services.analytics.aggregate_daily_metrics",
        "schedule": crontab(hour=1, minute=0),  # Daily at 1 AM
    },
    "refresh-materialized-views": {
        "task": "app.services.analytics.refresh_materialized_views",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes
    },
}
```

## Testing

### Unit Tests

```python
# backend/tests/services/test_telemetry.py
def test_create_session():
    session_data = SessionCreate(
        openid="test_user",
        ip_address="192.168.1.1",
        device_snapshot={...}
    )
    session = create_user_session(db, session_data)
    assert session.openid == "test_user"
```

### Integration Tests

```python
# backend/tests/api/routes/test_userinfo.py
def test_create_session_endpoint(client):
    response = client.post(
        "/api/v1/telemetry/session",
        json={
            "openid": "test_user",
            "ip_address": "192.168.1.1",
            "device_snapshot": {...}
        }
    )
    assert response.status_code == 201
```

### Run Tests

```bash
# Backend tests
docker compose exec backend bash scripts/test.sh

# Frontend E2E tests
cd frontend
npx playwright test
```

## Key Implementation Notes

### 1. Append-Only Pattern

AdInteraction table uses append-only pattern:
- No updates or deletes
- Use status field for soft deletes if needed
- Schema versioning via `schema_version` column

### 2. Data Tiering

- Hot data (0-7 days): Daily partitions
- Warm data (8-90 days): Monthly partitions in separate table
- Cold data (91-395 days): Quarterly partitions in archive table

### 3. Materialized Views

Refresh strategy:
```sql
REFRESH MATERIALIZED VIEW CONCURRENTLY hourly_activity_heatmap;
```

### 4. Risk Scoring

Real-time computation during interaction logging:
```python
risk_score = compute_risk_score(user_id, interaction_data)
if risk_score > threshold:
    apply_mitigation_action(user_id, risk_score)
```

### 5. IP Geolocation

Use MaxMind GeoIP2 database with fallback:
```python
location = geolocation_service.get_location(ip_address)
if not location:
    # Queue for batch processing
    queue_ip_for_processing(ip_address)
```

## Common Patterns

### Error Handling

```python
from fastapi import HTTPException

try:
    result = service.operation()
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
except NotFoundError:
    raise HTTPException(status_code=404, detail="Resource not found")
```

### Database Transactions

```python
from sqlmodel import Session

def operation_with_transaction(session: Session):
    try:
        # Multiple operations
        session.commit()
    except Exception:
        session.rollback()
        raise
```

### Background Task Retries

```python
@celery_app.task(bind=True, max_retries=3)
def process_task(self, data):
    try:
        # Process data
        pass
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
```

## Next Steps

1. **Review Data Model**: See [data-model.md](./data-model.md) for complete schema
2. **Review API Contracts**: See [contracts/openapi.yaml](./contracts/openapi.yaml) for API specification
3. **Review Research**: See [research.md](./research.md) for technical decisions
4. **Create Tasks**: Use `/speckit.tasks` to break down implementation into tasks
5. **Start Implementation**: Begin with P1 features (telemetry collection, interaction tracking)

## Resources

- **Specification**: [spec.md](./spec.md)
- **Implementation Plan**: [plan.md](./plan.md)
- **Data Model**: [data-model.md](./data-model.md)
- **API Contracts**: [contracts/openapi.yaml](./contracts/openapi.yaml)
- **Research**: [research.md](./research.md)
- **Constitution**: `.specify/memory/constitution.md`

