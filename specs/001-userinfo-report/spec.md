# Feature Specification: UserInfo Report

**Feature Branch**: `001-userinfo-report`  
**Created**: 2025-11-22  
**Status**: Draft  
**Input**: User description: "用户信息报告（UserInfo Report）"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Comprehensive User Information Collection (Priority: P1)

As a **system operator**, I need to collect and store comprehensive user information including basic identifiers, device characteristics, geographic location, and session timing so that I can build accurate user profiles for ad targeting and analytics.

**Why this priority**: User information collection is the foundational data layer that enables all reporting and analytics features. Without accurate user data capture, downstream reporting cannot function.

**Independent Test**: System can be tested by simulating user sessions with different device types, locations, and interaction patterns, then verifying all collected data is accurately stored and retrievable through reporting APIs.

**Acceptance Scenarios**:

1. **Given** a new user accesses the system for the first time, **When** their session begins, **Then** the system captures and persists: openid (immutable identifier), nickname (mutable profile), public IP address, session start timestamp, device OS family and version, device class (mobile/tablet/desktop), screen resolution, and screen density
2. **Given** a user's public IP address is captured, **When** the system processes location data, **Then** it derives and stores geolocation at country/city accuracy using IP intelligence services
3. **Given** a user grants location permission, **When** precise location data is available, **Then** the system stores opt-in location coordinates in addition to IP-derived location for enhanced targeting
4. **Given** a user's device information changes (e.g., screen rotation, app update), **When** a new session starts, **Then** the system updates device traits while preserving historical device snapshots for each ad interaction

---

### User Story 2 - Ad Interaction Behavior Tracking (Priority: P1)

As a **system operator**, I need to track all user interactions with ads including impressions, clicks, skips, completions, and dismissals so that I can analyze ad effectiveness and user engagement patterns.

**Why this priority**: Ad interaction tracking is essential for computing performance metrics (CTR, completion rates) and understanding user behavior, which directly informs ad serving optimization.

**Independent Test**: System can be tested by simulating various ad interaction sequences (impression → click → completion, impression → skip, etc.) and verifying all events are logged with correct timestamps, ad creative IDs, and session context.

**Acceptance Scenarios**:

1. **Given** an ad is displayed to a user, **When** the impression event occurs, **Then** the system logs: user_id, ad_type (interstitial/reward/banner), ad_creative_id, placement_id, timestamp, session_id, device snapshot, and location snapshot
2. **Given** a user clicks on an ad, **When** the click event occurs, **Then** the system logs: user_id, ad_creative_id, click_timestamp, time_since_impression, click_position (for banner ads), and session_context
3. **Given** a user skips or dismisses an ad, **When** the skip/dismissal event occurs, **Then** the system logs: user_id, ad_creative_id, skip_timestamp, time_watched (for video ads), skip_reason (if available), and session_context
4. **Given** a user completes watching a reward ad, **When** the completion event occurs, **Then** the system logs: user_id, ad_creative_id, completion_timestamp, total_watch_duration, reward_type, reward_amount, and verification_status
5. **Given** an ad fails to load or display, **When** the failure event occurs, **Then** the system logs: user_id, ad_type, failure_timestamp, error_code, error_message, and session_context

---

### User Story 3 - Time-Based Activity Analytics (Priority: P2)

As a **system operator**, I need to track user activity patterns across different time periods (hourly, daily, weekly) so that I can identify optimal ad serving windows and understand user engagement rhythms.

**Why this priority**: Time-based analytics enable data-driven decisions about when to serve ads for maximum engagement, but can be built after core tracking is in place.

**Independent Test**: System can be tested by generating activity data across multiple time periods and verifying time-based aggregations (hourly heatmaps, daily active users, peak activity windows) are accurately computed and reported.

**Acceptance Scenarios**:

1. **Given** users have activity across multiple hours of the day, **When** querying hourly activity patterns, **Then** the system returns a time-of-day heatmap showing: hour_of_day, active_user_count, total_impressions, total_clicks, average_session_duration
2. **Given** users have activity across multiple days, **When** querying daily activity trends, **Then** the system returns: date, daily_active_users, total_sessions, total_ad_interactions, average_sessions_per_user
3. **Given** a specific user has activity history, **When** querying that user's active time patterns, **Then** the system returns: user_id, preferred_hours (most active hours), average_session_start_time, average_session_duration, most_active_day_of_week

---

### User Story 4 - User Information Reporting Dashboard (Priority: P2)

As a **system operator**, I need to access comprehensive user information reports through a dashboard or API so that I can analyze individual user profiles, ad interaction history, and behavioral patterns for campaign optimization.

**Why this priority**: Reporting capabilities enable operators to make data-driven decisions, but depend on the foundational tracking features being implemented first.

**Independent Test**: System can be tested by querying user reports for test users with known interaction histories and verifying all expected data fields are present, accurate, and properly aggregated.

**Acceptance Scenarios**:

1. **Given** a user has accumulated interaction history, **When** querying user information report by user_id, **Then** the system returns: user profile (openid, nickname, registration_date), device information (current and historical), location information (IP-derived and opt-in), total impressions per ad type, click-through rate per ad type, completion rate for reward ads, skip rate, active time patterns, and risk score (if available)
2. **Given** multiple users exist in the system, **When** querying aggregate user reports with filters (device type, location, date range), **Then** the system returns: filtered user count, aggregate metrics (total impressions, average CTR, average completion rate), device distribution, geographic distribution, and time-based trends
3. **Given** operators need to analyze ad performance, **When** querying ad interaction reports, **Then** the system returns: impressions per ad creative, clicks per ad creative, CTR per ad creative, completion rates, skip rates, revenue metrics (if applicable), and user segment breakdowns
4. **Given** operators need to export data for external analysis, **When** requesting report export, **Then** the system generates downloadable reports in standard formats (CSV, JSON) containing all requested user and interaction data within privacy compliance boundaries

---

### Edge Cases

- **What happens when user's IP address changes during a session?** System captures IP at session start and logs IP changes as separate events, maintaining both original and updated IP for session context and fraud detection.

- **What happens when device information cannot be detected?** System logs available device traits (partial data) and marks missing fields as "unknown", allowing reporting to handle incomplete device profiles gracefully.

- **What happens when IP geolocation service is unavailable?** System logs IP address for later batch processing, marks location as "pending", and continues with other data collection. Location can be enriched retroactively when service is available.

- **What happens when user opts out of location tracking?** System respects opt-out flag, does not request precise location, uses IP-derived location only (with appropriate privacy notices), and excludes opt-out users from location-based targeting reports.

- **What happens when ad interaction events arrive out of order?** System uses event timestamps to reconstruct correct sequence, handles late-arriving events (e.g., impression logged after click), and maintains data consistency through event ordering logic.

- **What happens when reporting queries request data beyond retention period?** System returns available data within retention window, clearly indicates date range limitations, and provides guidance on accessing archived data if longer history is needed.

- **What happens when user has extremely high interaction volume (potential fraud)?** System continues logging all interactions, flags user for risk analysis, and includes risk indicators in user reports to support fraud detection workflows.

## Requirements *(mandatory)*

### Functional Requirements

**User Information Collection:**

- **FR-001**: System MUST capture and persist each user's immutable identifier (openid) for every ad-facing action
- **FR-002**: System MUST capture and persist each user's mutable profile information (nickname) with timestamp to track changes over time
- **FR-003**: System MUST capture and persist each user's network source (public IP address) for every session start
- **FR-004**: System MUST capture and persist session timing (start timestamp, end timestamp, duration) for every user session
- **FR-005**: System MUST enrich telemetry with device traits: OS family (iOS/Android/Web), OS version, device class (mobile/tablet/desktop), screen resolution (width x height), and screen density (DPI/PPI)
- **FR-006**: System MUST capture viewport metrics (viewport width, viewport height) to enable device-aware creative optimization
- **FR-007**: System MUST derive geolocation from IP address at minimum country/city accuracy using IP intelligence services
- **FR-008**: System SHOULD capture opt-in precise location coordinates (latitude, longitude) when user grants location permission, storing alongside IP-derived location
- **FR-009**: System MUST store device information snapshots at the time of each ad interaction to preserve historical device context

**Ad Interaction Tracking:**

- **FR-010**: System MUST log impressions (ad shown) with: user_id, ad_type, ad_creative_id, placement_id, timestamp, session_id, device snapshot, location snapshot
- **FR-011**: System MUST log clicks (ad engaged) with: user_id, ad_creative_id, click_timestamp, time_since_impression, click_position (for banner ads), session_context
- **FR-012**: System MUST log reward completions (ad fully watched) with: user_id, ad_creative_id, completion_timestamp, total_watch_duration, reward_type, reward_amount, verification_status
- **FR-013**: System MUST log dismissals (ad closed early) with: user_id, ad_creative_id, dismissal_timestamp, time_watched, dismissal_reason (if available)
- **FR-014**: System MUST log skips (ad skipped) with: user_id, ad_creative_id, skip_timestamp, time_watched, skip_reason
- **FR-015**: System MUST log failure states (ad failed to load/display) with: user_id, ad_type, failure_timestamp, error_code, error_message, session_context
- **FR-016**: System MUST compute and store daily aggregated metrics per user: click-through rate (CTR), completion rate, skip ratio
- **FR-017**: System MUST compute and store daily aggregated metrics per campaign: total impressions, total clicks, CTR, completion rate, skip ratio
- **FR-018**: System SHOULD expose aggregated ad interaction signals to reporting pipelines within 5 minutes of capture

**Time-Based Analytics:**

- **FR-019**: System MUST track user activity time patterns including: session start times, session end times, session durations, active hours of day
- **FR-020**: System MUST generate hourly activity heatmaps showing: hour_of_day, active_user_count, total_impressions, total_clicks, average_session_duration
- **FR-021**: System MUST generate daily activity trends showing: date, daily_active_users, total_sessions, total_ad_interactions, average_sessions_per_user
- **FR-022**: System MUST compute per-user active time patterns: preferred_hours (most active hours), average_session_start_time, average_session_duration, most_active_day_of_week

**Reporting Capabilities:**

- **FR-023**: System MUST provide user information report API that returns: user profile (openid, nickname, registration_date), device information (current and historical), location information, total impressions per ad type, CTR per ad type, completion rate, skip rate, active time patterns, risk score (if available)
- **FR-024**: System MUST provide aggregate user reports with filtering capabilities: filter by device type, filter by location (country/city), filter by date range, filter by user segment
- **FR-025**: System MUST provide ad interaction reports showing: impressions per ad creative, clicks per ad creative, CTR per ad creative, completion rates, skip rates, user segment breakdowns
- **FR-026**: System MUST support report export in standard formats (CSV, JSON) with configurable date ranges and field selections
- **FR-027**: System MUST enforce data retention rules: hot data (7 days) in fast stores, warm data (90 days) for experimentation, cold archive (13 months) for audits
- **FR-028**: System MUST validate data freshness: hot metrics available within 5 minutes, aggregate metrics available within 1 hour

**Privacy and Compliance:**

- **FR-029**: System MUST store telemetry in compliance with regional privacy laws, anonymizing or hashing PII where regulation demands
- **FR-030**: System MUST honor user opt-out flags for location tracking and exclude opt-out users from location-based reports
- **FR-031**: System MUST provide audit trails for data access, including: who accessed user data, when accessed, what data was accessed, purpose of access
- **FR-032**: System MUST retain audit trails for at least 13 months
- **FR-033**: System SHOULD surface transparency notices to users describing what telemetry is captured and how it is used

**Data Quality and Reliability:**

- **FR-034**: System MUST handle missing or incomplete device information gracefully, logging available data and marking missing fields appropriately
- **FR-035**: System MUST handle IP geolocation service unavailability by queuing IP addresses for batch processing and marking location as pending
- **FR-036**: System MUST handle out-of-order event arrival by using timestamps to reconstruct correct sequence
- **FR-037**: System MUST maintain data consistency when user information changes (e.g., nickname updates, device changes) by preserving historical snapshots

### Key Entities *(include if feature involves data)*

- **UserProfile**: Represents user identity and profile with attributes: openid (immutable unique identifier), nickname (mutable display name), registration_date, last_active_at, opt_out_flags (location tracking, etc.)

- **UserSession**: Represents a user session with attributes: session_id, user_id, start_timestamp, end_timestamp, duration, ip_address, device_snapshot (OS, device class, screen resolution, density), location_snapshot (country, city, coordinates if available)

- **AdInteraction**: Logs every ad event with attributes: interaction_id, user_id, session_id, ad_type (interstitial/reward/banner), ad_creative_id, placement_id, action (impression/click/skip/complete/dismiss/failure), timestamp, device_snapshot, location_snapshot, metadata (time_watched, click_position, error_code, etc.)

- **UserDeviceHistory**: Tracks device information changes over time with attributes: user_id, device_snapshot (OS, version, device class, screen resolution, density), first_seen_at, last_seen_at, interaction_count

- **UserLocationHistory**: Tracks location information with attributes: user_id, ip_address, ip_derived_location (country, city), precise_location (latitude, longitude, if opt-in), location_source (IP/precise), first_seen_at, last_seen_at

- **UserActivityPattern**: Aggregated time-based activity data with attributes: user_id, hour_of_day, day_of_week, average_session_start_time, average_session_duration, total_sessions, most_active_periods

- **DailyUserMetrics**: Daily aggregated metrics per user with attributes: user_id, date, total_impressions, total_clicks, total_completions, total_skips, ctr, completion_rate, skip_ratio

- **DailyCampaignMetrics**: Daily aggregated metrics per campaign with attributes: campaign_id, date, total_impressions, total_clicks, total_completions, total_skips, ctr, completion_rate, skip_ratio

- **UserReport**: Generated user information report with attributes: user_profile, device_history, location_history, activity_patterns, ad_interaction_summary, risk_indicators, report_generated_at

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System captures 100% of user device information (OS, device type, screen resolution) within 500ms of session start for all active users

- **SC-002**: System derives geolocation from IP address achieving city-level accuracy for 85%+ of users in supported regions

- **SC-003**: System logs 100% of ad interaction events (impressions, clicks, skips, completions, dismissals, failures) with complete metadata within 1 second of event occurrence

- **SC-004**: System computes and stores daily aggregated metrics (CTR, completion rate, skip ratio) per user and per campaign with 100% accuracy based on source interaction logs

- **SC-005**: System exposes aggregated ad interaction signals to reporting pipelines within 5 minutes of capture for 95%+ of events

- **SC-006**: System generates user information reports for any user within 2 seconds of query request, including complete interaction history and aggregated metrics

- **SC-007**: System generates aggregate reports with filters (device type, location, date range) within 5 seconds for date ranges up to 90 days

- **SC-008**: System maintains data freshness with hot metrics (last 7 days) available within 5 minutes and aggregate metrics available within 1 hour for 99%+ of queries

- **SC-009**: System handles 10,000+ concurrent user sessions while maintaining real-time data collection and reporting capabilities without degradation

- **SC-010**: System preserves historical device and location snapshots for 100% of ad interactions, enabling accurate retrospective analysis of user context at time of interaction
