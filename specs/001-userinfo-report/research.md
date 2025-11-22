# Research: UserInfo Report Technical Decisions

**Date**: 2025-11-22  
**Feature**: UserInfo Report  
**Purpose**: Document technical decisions for data storage, event logging, risk detection, and data tiering architecture.

## 1. Data Storage Architecture: Append-Only Event Store vs Relational

### Decision
**Hybrid approach**: Use PostgreSQL relational tables for structured data (UserProfile, UserSession, aggregated metrics) with append-only event logging pattern for AdInteraction events. Implement event sourcing principles where AdInteraction table acts as append-only log.

### Rationale
- **PostgreSQL strengths**: Existing infrastructure, ACID guarantees, complex queries, relationships, indexing
- **Event sourcing benefits**: Immutable audit trail, time-travel queries, replay capability for analytics
- **Hybrid approach**: Best of both worlds - structured queries for reports + immutable event log for compliance

### Implementation Strategy
- **AdInteraction table**: Primary key on (interaction_id, timestamp), no updates/deletes (soft deletes via status field)
- **Schema versioning**: Add `schema_version` column to AdInteraction for backwards compatibility
- **Historical snapshots**: Store device_snapshot and location_snapshot as JSONB columns to preserve context at time of event
- **Aggregated tables**: Materialized views or separate tables for DailyUserMetrics, DailyCampaignMetrics (updated via ETL)

### Alternatives Considered
- **Pure event store (Kafka, EventStore)**: Rejected - adds infrastructure complexity, PostgreSQL sufficient for current scale
- **Pure relational with updates**: Rejected - violates append-only requirement from constitution, loses audit trail
- **Time-series database (TimescaleDB)**: Considered but rejected - PostgreSQL with proper indexing sufficient, avoids additional dependency

## 2. Data Tiering Strategy (Hot/Warm/Cold)

### Decision
**PostgreSQL table partitioning + archive tables**: Use PostgreSQL native partitioning for hot data (7 days), separate warm table (90 days), and cold archive table (13 months) with automated data movement via scheduled jobs.

### Rationale
- **PostgreSQL partitioning**: Native feature, no additional infrastructure, efficient querying within partitions
- **Partition pruning**: Queries automatically filter to relevant partitions based on date ranges
- **Cost-effective**: Single database instance, no need for separate storage tiers initially
- **Scalability path**: Can migrate to separate databases or object storage (S3) for cold data if needed

### Implementation Strategy
- **Hot data (0-7 days)**: Partitioned table `ad_interaction` with daily partitions, indexed for fast queries
- **Warm data (8-90 days)**: Separate table `ad_interaction_warm` with monthly partitions, less frequent indexing
- **Cold data (91-395 days)**: Archive table `ad_interaction_archive` with quarterly partitions, minimal indexes, read-only
- **Data movement**: Scheduled Celery/Background tasks or PostgreSQL pg_cron extension to move data between tiers
- **Retention enforcement**: Automated deletion of data older than 13 months from archive

### Alternatives Considered
- **Separate databases**: Rejected - adds operational complexity, connection management overhead
- **Object storage (S3) for cold**: Considered for future - acceptable for Phase 1 to use archive table, can migrate later
- **Time-series database with retention policies**: Rejected - PostgreSQL partitioning sufficient, avoids new dependency

## 3. Derived Tables and Materialized Views Strategy

### Decision
**Materialized views for aggregations + real-time computation for reports**: Use PostgreSQL materialized views for time-based aggregations (hourly heatmaps, daily metrics) refreshed periodically, with real-time computation for on-demand user reports.

### Rationale
- **Materialized views**: Pre-computed aggregations reduce query load, fast reads for dashboards
- **Refresh strategy**: Incremental refresh possible with PostgreSQL 13+ (REFRESH MATERIALIZED VIEW CONCURRENTLY)
- **Real-time computation**: User reports query recent data directly from source tables for freshness
- **Balance**: Pre-compute common queries (heatmaps, daily trends), compute on-demand for user-specific reports

### Implementation Strategy
- **Materialized views**:
  - `hourly_activity_heatmap`: Refreshed every 15 minutes
  - `daily_user_metrics`: Refreshed hourly
  - `daily_campaign_metrics`: Refreshed hourly
- **Real-time queries**: User reports, aggregate reports with filters query source tables directly
- **Indexing**: Composite indexes on (user_id, timestamp), (ad_creative_id, date) for fast lookups

### Alternatives Considered
- **Pure real-time computation**: Rejected - too slow for dashboard queries, high database load
- **Pure materialized views for everything**: Rejected - user reports need fresh data, too many views to maintain
- **OLAP database (ClickHouse, Druid)**: Considered for future - acceptable for Phase 1 to use PostgreSQL, can add later if scale demands

## 4. Risk and Fraud Detection Implementation

### Decision
**Rule-based risk scoring service with configurable thresholds**: Implement Python service that computes risk scores based on behavioral patterns, with progressive response tiers and audit logging.

### Rationale
- **Rule-based approach**: Transparent, debuggable, no ML infrastructure needed initially
- **Configurable thresholds**: Operators can adjust sensitivity without code changes
- **Real-time computation**: Risk scores computed on-demand during ad interaction logging
- **Audit trail**: All risk decisions logged to RiskDecisionAudit table for compliance

### Implementation Strategy
- **Risk scoring factors**:
  - Click velocity: Clicks per minute, clicks per session (threshold: >10/min, >50/session)
  - Session patterns: Unusual session duration, rapid session creation
  - Device fingerprint consistency: Device changes within short time window
  - IP reputation: IP-based risk indicators (future: integrate with IP reputation service)
  - Historical fraud indicators: Previous risk flags, suspension history
- **Risk score calculation**: Weighted sum of risk factors (0-100 scale)
- **Response tiers**:
  1. Observation (score 30-50): Log suspicious activity, no action
  2. Rate limiting (score 51-70): Temporary cooldown periods between interactions
  3. Shadow-banning (score 71-85): Ads served but not credited, interactions logged
  4. Temporary suspension (score 86-100): Block ad interactions for configurable duration
- **Service architecture**: `backend/app/services/risk_scoring.py` with async computation, cached risk scores (Redis optional for Phase 1)

### Alternatives Considered
- **ML-based fraud detection**: Considered for future - acceptable for Phase 1 to use rule-based, can add ML later
- **Third-party fraud detection service**: Rejected - adds external dependency, cost, data privacy concerns
- **Batch-only risk scoring**: Rejected - constitution requires real-time detection

## 5. Ad Delivery Health Monitoring

### Decision
**Background monitoring service with alerting**: Implement service that periodically checks impression-to-request ratios, fill rates, and delivery health metrics, with configurable alerting thresholds.

### Rationale
- **Proactive monitoring**: Detect issues before they impact users
- **Configurable thresholds**: Operators can adjust alert sensitivity
- **Audit trail**: All health checks logged for trend analysis
- **Integration**: Can integrate with existing monitoring (Sentry) or add new alerting system

### Implementation Strategy
- **Metrics tracked**:
  - Impression-to-request ratio: Requests vs successful impressions (threshold: <50% alerts)
  - Fill rate per ad type: Interstitial, reward, banner fill rates (threshold: <80% alerts)
  - Delivery latency: Time from request to impression (threshold: >5s alerts)
- **Monitoring frequency**: Every 5 minutes for hot metrics, hourly for aggregate trends
- **Alerting**: Log to monitoring system (Sentry), optional: email/Slack notifications for critical thresholds
- **Service architecture**: `backend/app/services/delivery_health.py` with scheduled background tasks

### Alternatives Considered
- **Real-time monitoring on every request**: Rejected - too high overhead, periodic checks sufficient
- **External monitoring service**: Rejected - adds dependency, can use existing infrastructure
- **Manual monitoring only**: Rejected - constitution requires automated validation

## 6. ETL Pipelines and Data Freshness Validation

### Decision
**Background task system (Celery) with data freshness validation**: Use Celery for ETL jobs (aggregation, data movement, risk scoring), with validation checks that alert when data freshness thresholds are exceeded.

### Rationale
- **Celery**: Standard Python task queue, integrates with FastAPI, supports scheduled tasks
- **Data freshness validation**: Automated checks ensure SLAs are met (5 min hot, 1 hour aggregates)
- **Alerting**: Integration with monitoring system for SLA violations
- **Scalability**: Can scale workers independently, supports distributed processing

### Implementation Strategy
- **ETL jobs**:
  - `aggregate_daily_metrics`: Runs hourly, computes daily user/campaign metrics
  - `refresh_materialized_views`: Runs every 15 minutes for hourly heatmaps
  - `move_data_to_warm`: Runs daily, moves 7-day-old data to warm table
  - `move_data_to_archive`: Runs weekly, moves 90-day-old data to archive
- **Data freshness validation**:
  - Check: Latest event timestamp vs current time (threshold: >5 min lag alerts)
  - Check: Latest aggregate timestamp vs current time (threshold: >1 hour lag alerts)
  - Service: `backend/app/services/data_freshness.py` with scheduled validation tasks
- **Monitoring**: Log freshness metrics, alert on threshold violations

### Alternatives Considered
- **PostgreSQL pg_cron only**: Considered - simpler but less flexible, Celery provides better error handling and retries
- **Apache Airflow**: Rejected - overkill for current scale, adds infrastructure complexity
- **No ETL, pure real-time**: Rejected - too slow for aggregations, high database load

## 7. IP Geolocation Service Integration

### Decision
**MaxMind GeoIP2 or ipapi.co with fallback strategy**: Use commercial IP geolocation service (MaxMind GeoIP2 database or ipapi.co API) with graceful degradation when service unavailable.

### Rationale
- **Accuracy**: Commercial services provide city-level accuracy required by spec (85%+)
- **Fallback strategy**: Queue IPs for batch processing when service unavailable, mark location as pending
- **Cost-effective**: MaxMind GeoIP2 database (one-time cost) or ipapi.co API (pay-per-use)
- **Privacy**: IP addresses are not PII, but should be handled according to privacy policy

### Implementation Strategy
- **Primary**: MaxMind GeoIP2 database (local database file, updated monthly) for fast lookups
- **Fallback**: ipapi.co API for real-time lookups if database unavailable
- **Service architecture**: `backend/app/services/geolocation.py` with caching, batch processing queue
- **Error handling**: Log IP for later processing if service unavailable, continue with other data collection

### Alternatives Considered
- **Free IP geolocation APIs only**: Rejected - may not meet 85% accuracy requirement, rate limits
- **No geolocation**: Rejected - required by constitution and spec
- **Self-hosted geolocation**: Rejected - too complex, commercial services more accurate

## Summary of Technical Decisions

| Decision Area | Chosen Approach | Key Rationale |
|--------------|----------------|---------------|
| Event Storage | Hybrid: Relational + append-only pattern | PostgreSQL sufficient, event sourcing benefits |
| Data Tiering | PostgreSQL partitioning + archive tables | Native feature, cost-effective, scalable |
| Aggregations | Materialized views + real-time queries | Balance performance and freshness |
| Risk Detection | Rule-based scoring service | Transparent, debuggable, real-time |
| Delivery Health | Background monitoring service | Proactive issue detection |
| ETL Pipelines | Celery background tasks | Standard Python solution, scalable |
| Geolocation | MaxMind GeoIP2 + ipapi.co fallback | Accuracy + reliability |

All decisions align with existing technology stack (FastAPI, PostgreSQL, Python) and can be implemented without adding major new infrastructure dependencies.

