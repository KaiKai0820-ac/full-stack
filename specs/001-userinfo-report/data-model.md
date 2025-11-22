# Data Model: UserInfo Report

**Date**: 2025-11-22  
**Feature**: UserInfo Report  
**Database**: PostgreSQL  
**ORM**: SQLModel

## Overview

The UserInfo Report feature extends the existing database schema with new models for user telemetry, ad interaction tracking, analytics, and reporting. All models follow the existing patterns (UUID primary keys, SQLModel, Pydantic validation).

## Core Entities

### 1. UserProfile

**Purpose**: Represents user identity and profile information.

**Table**: `userprofile`

**Fields**:
- `id` (UUID, PK): Unique identifier (maps to existing User.id or separate table)
- `openid` (String, unique, indexed): Immutable unique identifier for ad-facing actions
- `nickname` (String, nullable): Mutable display name
- `registration_date` (DateTime): When user first registered
- `last_active_at` (DateTime, indexed): Last activity timestamp
- `opt_out_flags` (JSONB): Flags for opt-out preferences (location_tracking, personalized_ads, etc.)
- `created_at` (DateTime): Record creation timestamp
- `updated_at` (DateTime): Record update timestamp

**Relationships**:
- One-to-many: UserSession, AdInteraction, UserDeviceHistory, UserLocationHistory, UserActivityPattern, DailyUserMetrics

**Validation Rules**:
- `openid` must be unique and non-null
- `opt_out_flags` must be valid JSON object

**State Transitions**: None (immutable openid, mutable nickname)

### 2. UserSession

**Purpose**: Represents a user session with device and location snapshots.

**Table**: `usersession`

**Fields**:
- `id` (UUID, PK): Session identifier
- `user_id` (UUID, FK → UserProfile.id, indexed): Reference to user
- `start_timestamp` (DateTime, indexed): Session start time
- `end_timestamp` (DateTime, nullable): Session end time
- `duration` (Integer, seconds): Calculated duration
- `ip_address` (String, indexed): Public IP address at session start
- `device_snapshot` (JSONB): Device information at session start
  - `os_family` (String): iOS/Android/Web
  - `os_version` (String): OS version
  - `device_class` (String): mobile/tablet/desktop
  - `screen_resolution` (String): "widthxheight"
  - `screen_density` (Float): DPI/PPI
  - `viewport_width` (Integer): Viewport width
  - `viewport_height` (Integer): Viewport height
- `location_snapshot` (JSONB): Location information at session start
  - `country` (String): Country code
  - `city` (String): City name
  - `latitude` (Float, nullable): Precise latitude if opt-in
  - `longitude` (Float, nullable): Precise longitude if opt-in
  - `location_source` (String): "IP" or "precise"
- `created_at` (DateTime): Record creation timestamp

**Relationships**:
- Many-to-one: UserProfile
- One-to-many: AdInteraction

**Validation Rules**:
- `start_timestamp` must be before `end_timestamp` if both present
- `device_snapshot` must contain required fields (os_family, device_class)
- `location_snapshot` must contain country at minimum

**Indexes**:
- `(user_id, start_timestamp)` for user session queries
- `(start_timestamp)` for time-based queries

### 3. AdInteraction

**Purpose**: Append-only event log for all ad interactions (impressions, clicks, completions, skips, dismissals, failures).

**Table**: `ad_interaction` (partitioned by date for hot data)

**Fields**:
- `interaction_id` (UUID, PK): Unique interaction identifier
- `user_id` (UUID, FK → UserProfile.id, indexed): Reference to user
- `session_id` (UUID, FK → UserSession.id, indexed): Reference to session
- `ad_type` (String, indexed): "interstitial", "reward", "banner"
- `ad_creative_id` (String, indexed): Ad creative identifier
- `placement_id` (String, indexed): Placement identifier
- `action` (String, indexed): "impression", "click", "skip", "complete", "dismiss", "failure"
- `timestamp` (DateTime, indexed): Event timestamp (used for partitioning)
- `device_snapshot` (JSONB): Device information at time of interaction (preserves historical context)
- `location_snapshot` (JSONB): Location information at time of interaction
- `metadata` (JSONB): Action-specific metadata
  - For clicks: `time_since_impression` (Integer, seconds), `click_position` (Object, for banners)
  - For skips/dismissals: `time_watched` (Integer, seconds), `skip_reason` (String, nullable)
  - For completions: `total_watch_duration` (Integer, seconds), `reward_type` (String), `reward_amount` (Float), `verification_status` (String)
  - For failures: `error_code` (String), `error_message` (String)
- `schema_version` (Integer): Schema version for backwards compatibility
- `created_at` (DateTime): Record creation timestamp (immutable)

**Relationships**:
- Many-to-one: UserProfile, UserSession

**Validation Rules**:
- `action` must be one of: impression, click, skip, complete, dismiss, failure
- `ad_type` must be one of: interstitial, reward, banner
- `metadata` structure must match `action` type
- No updates or deletes (append-only pattern)

**Indexes**:
- `(user_id, timestamp)` for user interaction history
- `(ad_creative_id, timestamp)` for ad performance queries
- `(action, timestamp)` for action-type queries
- `(timestamp)` for partitioning and time-based queries

**Partitioning Strategy**:
- Hot data (0-7 days): Daily partitions in `ad_interaction` table
- Warm data (8-90 days): Monthly partitions in `ad_interaction_warm` table
- Cold data (91-395 days): Quarterly partitions in `ad_interaction_archive` table

### 4. UserDeviceHistory

**Purpose**: Tracks device information changes over time.

**Table**: `userdevicehistory`

**Fields**:
- `id` (UUID, PK): Record identifier
- `user_id` (UUID, FK → UserProfile.id, indexed): Reference to user
- `device_snapshot` (JSONB): Device information (same structure as UserSession.device_snapshot)
- `first_seen_at` (DateTime, indexed): First time this device configuration was seen
- `last_seen_at` (DateTime, indexed): Last time this device configuration was seen
- `interaction_count` (Integer): Number of interactions with this device configuration
- `created_at` (DateTime): Record creation timestamp
- `updated_at` (DateTime): Record update timestamp

**Relationships**:
- Many-to-one: UserProfile

**Validation Rules**:
- `device_snapshot` must contain required fields
- `first_seen_at` must be before or equal to `last_seen_at`

**Indexes**:
- `(user_id, last_seen_at)` for user device history queries

### 5. UserLocationHistory

**Purpose**: Tracks location information changes over time.

**Table**: `userlocationhistory`

**Fields**:
- `id` (UUID, PK): Record identifier
- `user_id` (UUID, FK → UserProfile.id, indexed): Reference to user
- `ip_address` (String, indexed): IP address
- `ip_derived_location` (JSONB): IP-derived location
  - `country` (String)
  - `city` (String)
- `precise_location` (JSONB, nullable): Opt-in precise location
  - `latitude` (Float)
  - `longitude` (Float)
- `location_source` (String): "IP" or "precise"
- `first_seen_at` (DateTime, indexed): First time this location was seen
- `last_seen_at` (DateTime, indexed): Last time this location was seen
- `created_at` (DateTime): Record creation timestamp
- `updated_at` (DateTime): Record update timestamp

**Relationships**:
- Many-to-one: UserProfile

**Validation Rules**:
- `ip_derived_location` must contain country at minimum
- `precise_location` requires both latitude and longitude if present
- `location_source` must be "IP" or "precise"

**Indexes**:
- `(user_id, last_seen_at)` for user location history queries
- `(ip_address)` for IP-based queries

### 6. UserActivityPattern

**Purpose**: Aggregated time-based activity data per user.

**Table**: `useractivitypattern`

**Fields**:
- `id` (UUID, PK): Record identifier
- `user_id` (UUID, FK → UserProfile.id, indexed, unique per hour/day): Reference to user
- `hour_of_day` (Integer, 0-23): Hour of day for this pattern
- `day_of_week` (Integer, 0-6): Day of week (0=Monday)
- `average_session_start_time` (Time): Average session start time for this hour/day
- `average_session_duration` (Integer, seconds): Average session duration
- `total_sessions` (Integer): Total sessions in this time pattern
- `most_active_periods` (JSONB): Array of most active time periods
- `computed_at` (DateTime): When this pattern was computed
- `created_at` (DateTime): Record creation timestamp
- `updated_at` (DateTime): Record update timestamp

**Relationships**:
- Many-to-one: UserProfile

**Validation Rules**:
- `hour_of_day` must be 0-23
- `day_of_week` must be 0-6
- `average_session_duration` must be non-negative

**Indexes**:
- `(user_id, hour_of_day, day_of_week)` for user pattern queries
- `(hour_of_day, day_of_week)` for time-based analytics

### 7. DailyUserMetrics

**Purpose**: Daily aggregated metrics per user.

**Table**: `dailyusermetrics`

**Fields**:
- `id` (UUID, PK): Record identifier
- `user_id` (UUID, FK → UserProfile.id, indexed): Reference to user
- `date` (Date, indexed): Metric date
- `total_impressions` (Integer): Total impressions on this date
- `total_clicks` (Integer): Total clicks on this date
- `total_completions` (Integer): Total completions on this date
- `total_skips` (Integer): Total skips on this date
- `ctr` (Float): Click-through rate (clicks/impressions)
- `completion_rate` (Float): Completion rate (completions/impressions)
- `skip_ratio` (Float): Skip ratio (skips/impressions)
- `computed_at` (DateTime): When metrics were computed
- `created_at` (DateTime): Record creation timestamp
- `updated_at` (DateTime): Record update timestamp

**Relationships**:
- Many-to-one: UserProfile

**Validation Rules**:
- `ctr`, `completion_rate`, `skip_ratio` must be between 0 and 1
- Unique constraint on `(user_id, date)`

**Indexes**:
- `(user_id, date)` for user daily metrics queries
- `(date)` for date-based aggregations

### 8. DailyCampaignMetrics

**Purpose**: Daily aggregated metrics per campaign/ad creative.

**Table**: `dailycampaignmetrics`

**Fields**:
- `id` (UUID, PK): Record identifier
- `campaign_id` (String, indexed): Campaign identifier (or ad_creative_id)
- `date` (Date, indexed): Metric date
- `total_impressions` (Integer): Total impressions on this date
- `total_clicks` (Integer): Total clicks on this date
- `total_completions` (Integer): Total completions on this date
- `total_skips` (Integer): Total skips on this date
- `ctr` (Float): Click-through rate
- `completion_rate` (Float): Completion rate
- `skip_ratio` (Float): Skip ratio
- `computed_at` (DateTime): When metrics were computed
- `created_at` (DateTime): Record creation timestamp
- `updated_at` (DateTime): Record update timestamp

**Validation Rules**:
- `ctr`, `completion_rate`, `skip_ratio` must be between 0 and 1
- Unique constraint on `(campaign_id, date)`

**Indexes**:
- `(campaign_id, date)` for campaign daily metrics queries
- `(date)` for date-based aggregations

### 9. UserReport (Virtual/Computed)

**Purpose**: Generated user information report (not a database table, computed from other entities).

**Computed Fields** (from other entities):
- `user_profile`: From UserProfile
- `device_history`: From UserDeviceHistory (all records for user)
- `location_history`: From UserLocationHistory (all records for user)
- `activity_patterns`: From UserActivityPattern (all records for user)
- `ad_interaction_summary`: Aggregated from AdInteraction
  - `total_impressions_per_ad_type`: Grouped by ad_type
  - `ctr_per_ad_type`: Grouped by ad_type
  - `completion_rate`: For reward ads
  - `skip_rate`: Overall skip rate
- `risk_indicators`: From RiskDecisionAudit (if available)
- `report_generated_at`: Timestamp when report was generated

### 10. RiskDecisionAudit

**Purpose**: Audit log for risk scoring and fraud detection decisions.

**Table**: `riskdecisionaudit`

**Fields**:
- `id` (UUID, PK): Record identifier
- `user_id` (UUID, FK → UserProfile.id, indexed): Reference to user
- `risk_score` (Float): Computed risk score (0-100)
- `triggering_factors` (JSONB): Array of factors that contributed to risk score
  - `click_velocity` (Float): Clicks per minute
  - `session_patterns` (Object): Unusual session indicators
  - `device_fingerprint_consistency` (Float): Device consistency score
  - `ip_reputation` (Float, nullable): IP reputation score
  - `historical_fraud_indicators` (Array): Previous risk flags
- `mitigation_action` (String): Action taken: "observation", "rate_limit", "shadow_ban", "suspension"
- `action_duration` (Integer, seconds, nullable): Duration of mitigation action
- `decision_timestamp` (DateTime, indexed): When decision was made
- `created_at` (DateTime): Record creation timestamp

**Relationships**:
- Many-to-one: UserProfile

**Validation Rules**:
- `risk_score` must be between 0 and 100
- `mitigation_action` must be one of: observation, rate_limit, shadow_ban, suspension

**Indexes**:
- `(user_id, decision_timestamp)` for user risk history
- `(decision_timestamp)` for time-based risk analysis

## Materialized Views

### 1. hourly_activity_heatmap

**Purpose**: Pre-computed hourly activity aggregations for dashboard queries.

**Refresh Strategy**: Every 15 minutes (CONCURRENTLY)

**Fields**:
- `hour_of_day` (Integer, PK): Hour (0-23)
- `date` (Date, PK): Date
- `active_user_count` (Integer): Distinct users active in this hour
- `total_impressions` (Integer): Total impressions in this hour
- `total_clicks` (Integer): Total clicks in this hour
- `average_session_duration` (Float): Average session duration in seconds

**Indexes**:
- `(date, hour_of_day)` for time-based queries

## Data Retention and Archival

### Retention Rules
- **Hot data (0-7 days)**: `ad_interaction` table with daily partitions
- **Warm data (8-90 days)**: `ad_interaction_warm` table with monthly partitions
- **Cold data (91-395 days)**: `ad_interaction_archive` table with quarterly partitions
- **Permanent**: UserProfile, UserSession (metadata), aggregated metrics tables

### Archival Strategy
- Automated data movement via scheduled Celery tasks
- Data older than 13 months automatically deleted from archive
- UserProfile and aggregated metrics retained permanently for reporting

## Schema Versioning

### AdInteraction Schema Versioning
- `schema_version` column in `ad_interaction` table
- Version 1: Initial schema
- Future versions: Add new fields to `metadata` JSONB, increment version
- Backwards compatibility: Code handles multiple schema versions

## Relationships Diagram

```
UserProfile (1) ──< (N) UserSession
UserProfile (1) ──< (N) AdInteraction
UserProfile (1) ──< (N) UserDeviceHistory
UserProfile (1) ──< (N) UserLocationHistory
UserProfile (1) ──< (N) UserActivityPattern
UserProfile (1) ──< (N) DailyUserMetrics
UserProfile (1) ──< (N) RiskDecisionAudit

UserSession (1) ──< (N) AdInteraction
```

## Indexing Strategy

### High-Frequency Queries
- User interaction history: `(user_id, timestamp)` on AdInteraction
- Ad performance: `(ad_creative_id, timestamp)` on AdInteraction
- Time-based analytics: `(timestamp)` on AdInteraction (partitioning key)
- User reports: `(user_id)` indexes on all user-related tables

### Aggregation Queries
- Daily metrics: `(user_id, date)` on DailyUserMetrics
- Campaign metrics: `(campaign_id, date)` on DailyCampaignMetrics
- Activity patterns: `(hour_of_day, day_of_week)` on UserActivityPattern

## Data Validation and Constraints

### Required Fields
- All primary keys and foreign keys are non-nullable
- UserProfile.openid must be unique and non-null
- AdInteraction.action must be one of valid actions
- All timestamp fields must be valid DateTime values

### Business Rules
- Session duration must be non-negative
- CTR, completion_rate, skip_ratio must be between 0 and 1
- Risk scores must be between 0 and 100
- Device snapshots must contain required fields (os_family, device_class)

