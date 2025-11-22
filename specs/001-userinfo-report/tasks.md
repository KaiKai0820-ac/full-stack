# Tasks: UserInfo Report

**Input**: Design documents from `/specs/001-userinfo-report/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: Which user story this task belongs to (e.g., [US1], [US2], [US3], [US4])
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/app/`, `frontend/src/` (per plan.md structure)
- Backend models: `backend/app/models.py` (extend existing)
- Backend services: `backend/app/services/`
- Backend routes: `backend/app/api/routes/`
- Frontend components: `frontend/src/components/UserInfo/`
- Tests: `backend/tests/`, `frontend/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create database migration directory structure in backend/alembic/versions/ for UserInfo Report migrations
- [X] T002 [P] Add MaxMind GeoIP2 dependency to backend/requirements.txt (geoip2 package)
- [X] T003 [P] Add Celery dependency to backend/requirements.txt (celery, redis packages)
- [X] T004 [P] Configure Celery broker and result backend in backend/app/core/config.py
- [X] T005 [P] Create backend/app/services/__init__.py if missing

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 Create database migration for UserProfile model in backend/alembic/versions/ (base entity for all stories)
- [X] T007 [P] Create database migration for UserSession model in backend/alembic/versions/ (needed by US1, US2)
- [X] T008 [P] Create database migration for AdInteraction table with partitioning setup in backend/alembic/versions/ (needed by US2)
- [X] T009 [P] Create database migration for UserDeviceHistory model in backend/alembic/versions/ (needed by US1)
- [X] T010 [P] Create database migration for UserLocationHistory model in backend/alembic/versions/ (needed by US1)
- [X] T011 [P] Create database migration for UserActivityPattern model in backend/alembic/versions/ (needed by US3)
- [X] T012 [P] Create database migration for DailyUserMetrics model in backend/alembic/versions/ (needed by US4)
- [X] T013 [P] Create database migration for DailyCampaignMetrics model in backend/alembic/versions/ (needed by US4)
- [X] T014 [P] Create database migration for RiskDecisionAudit model in backend/alembic/versions/ (needed by US4)
- [X] T015 [P] Create database migration for materialized view hourly_activity_heatmap in backend/alembic/versions/ (needed by US3)
- [X] T016 Create UserProfile SQLModel in backend/app/models.py (base entity)
- [X] T017 [P] Create UserSession SQLModel in backend/app/models.py
- [X] T018 [P] Create AdInteraction SQLModel in backend/app/models.py
- [X] T019 [P] Create UserDeviceHistory SQLModel in backend/app/models.py
- [X] T020 [P] Create UserLocationHistory SQLModel in backend/app/models.py
- [X] T021 [P] Create UserActivityPattern SQLModel in backend/app/models.py
- [X] T022 [P] Create DailyUserMetrics SQLModel in backend/app/models.py
- [X] T023 [P] Create DailyCampaignMetrics SQLModel in backend/app/models.py
- [X] T024 [P] Create RiskDecisionAudit SQLModel in backend/app/models.py
- [X] T025 Setup database partitioning for ad_interaction table (hot data 0-7 days) in backend/alembic/versions/
- [X] T026 Create ad_interaction_warm table structure in backend/alembic/versions/ (warm data 8-90 days)
- [X] T027 Create ad_interaction_archive table structure in backend/alembic/versions/ (cold data 91-395 days)
- [X] T028 Configure IP geolocation service (MaxMind GeoIP2) in backend/app/services/geolocation.py
- [X] T029 [P] Add geolocation configuration settings to backend/app/core/config.py (MaxMind database path, ipapi.co API key)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Comprehensive User Information Collection (Priority: P1) 🎯 MVP

**Goal**: Collect and store comprehensive user information including identifiers, device characteristics, geographic location, and session timing.

**Independent Test**: System can be tested by simulating user sessions with different device types, locations, and interaction patterns, then verifying all collected data is accurately stored and retrievable through reporting APIs.

### Implementation for User Story 1

- [X] T030 [P] [US1] Implement telemetry collection service in backend/app/services/telemetry.py (create session, capture device/location)
- [X] T031 [US1] Implement geolocation enrichment service in backend/app/services/geolocation.py (IP to country/city, opt-in location handling)
- [X] T032 [US1] Implement POST /telemetry/session endpoint in backend/app/api/routes/telemetry.py (creates session, captures device/location)
- [X] T033 [US1] Implement PATCH /telemetry/session/{session_id} endpoint in backend/app/api/routes/telemetry.py (updates session end time)
- [X] T034 [US1] Add CRUD operations for UserProfile in backend/app/crud.py (create/update user profile)
- [X] T035 [US1] Add CRUD operations for UserSession in backend/app/crud.py (create/update session)
- [X] T036 [US1] Add CRUD operations for UserDeviceHistory in backend/app/crud.py (track device changes)
- [X] T037 [US1] Add CRUD operations for UserLocationHistory in backend/app/crud.py (track location changes)
- [X] T038 [US1] Add validation for device snapshot schema in backend/app/services/telemetry.py (os_family, device_class required)
- [X] T039 [US1] Add validation for location snapshot schema in backend/app/services/telemetry.py (country required, opt-in location optional)
- [X] T040 [US1] Implement device snapshot preservation logic in backend/app/services/telemetry.py (store device info at session start)
- [X] T041 [US1] Implement location snapshot preservation logic in backend/app/services/telemetry.py (store location at session start)
- [X] T042 [US1] Add error handling for missing device information in backend/app/services/telemetry.py (mark fields as "unknown")
- [X] T043 [US1] Add error handling for geolocation service unavailability in backend/app/services/geolocation.py (queue IPs, mark location as pending)
- [X] T044 [US1] Add opt-out flag handling for location tracking in backend/app/services/telemetry.py (respect opt_out_flags)
- [X] T045 [US1] Add logging for telemetry collection operations in backend/app/services/telemetry.py
- [X] T046 [US1] Register telemetry routes in backend/app/api/main.py

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. System can create user sessions, capture device/location information, and store all required telemetry data.

---

## Phase 4: User Story 2 - Ad Interaction Behavior Tracking (Priority: P1) 🎯 MVP

**Goal**: Track all user interactions with ads including impressions, clicks, skips, completions, and dismissals.

**Independent Test**: System can be tested by simulating various ad interaction sequences (impression → click → completion, impression → skip, etc.) and verifying all events are logged with correct timestamps, ad creative IDs, and session context.

### Implementation for User Story 2

- [ ] T047 [P] [US2] Implement ad interaction logging service in backend/app/services/interactions.py (log impressions, clicks, skips, completions, dismissals, failures)
- [ ] T048 [US2] Implement POST /interactions endpoint in backend/app/api/routes/interactions.py (logs ad interaction events)
- [ ] T049 [US2] Implement GET /interactions/{interaction_id} endpoint in backend/app/api/routes/interactions.py (retrieves interaction by ID)
- [ ] T050 [US2] Add CRUD operations for AdInteraction in backend/app/crud.py (append-only pattern, no updates/deletes)
- [ ] T051 [US2] Implement append-only event logging pattern in backend/app/services/interactions.py (no updates/deletes, schema versioning)
- [ ] T052 [US2] Add validation for ad interaction action types in backend/app/services/interactions.py (impression, click, skip, complete, dismiss, failure)
- [ ] T053 [US2] Add validation for ad type enum in backend/app/services/interactions.py (interstitial, reward, banner)
- [ ] T054 [US2] Implement metadata structure validation per action type in backend/app/services/interactions.py (click metadata, skip metadata, completion metadata, failure metadata)
- [ ] T055 [US2] Implement device/location snapshot capture at interaction time in backend/app/services/interactions.py (preserve historical context)
- [ ] T056 [US2] Add error handling for out-of-order event arrival in backend/app/services/interactions.py (use timestamps to reconstruct sequence)
- [ ] T057 [US2] Implement daily aggregation service for user metrics in backend/app/services/analytics.py (compute CTR, completion rate, skip ratio per user)
- [ ] T058 [US2] Implement daily aggregation service for campaign metrics in backend/app/services/analytics.py (compute CTR, completion rate, skip ratio per campaign)
- [ ] T059 [US2] Create Celery task for daily metrics aggregation in backend/app/services/tasks.py (runs hourly, computes daily metrics)
- [ ] T060 [US2] Add logging for ad interaction operations in backend/app/services/interactions.py
- [ ] T061 [US2] Register interaction routes in backend/app/api/main.py

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently. System can log all ad interactions, preserve historical snapshots, and compute daily aggregated metrics.

---

## Phase 5: User Story 3 - Time-Based Activity Analytics (Priority: P2)

**Goal**: Track user activity patterns across different time periods (hourly, daily, weekly) for optimal ad serving windows and engagement analysis.

**Independent Test**: System can be tested by generating activity data across multiple time periods and verifying time-based aggregations (hourly heatmaps, daily active users, peak activity windows) are accurately computed and reported.

### Implementation for User Story 3

- [ ] T062 [P] [US3] Implement time-based analytics computation service in backend/app/services/analytics.py (hourly heatmaps, daily trends, user patterns)
- [ ] T063 [US3] Implement GET /analytics/hourly endpoint in backend/app/api/routes/analytics.py (returns hourly activity heatmap)
- [ ] T064 [US3] Implement GET /analytics/daily endpoint in backend/app/api/routes/analytics.py (returns daily activity trends)
- [ ] T065 [US3] Implement GET /analytics/user/{user_id}/patterns endpoint in backend/app/api/routes/analytics.py (returns user activity patterns)
- [ ] T066 [US3] Add CRUD operations for UserActivityPattern in backend/app/crud.py (create/update activity patterns)
- [ ] T067 [US3] Implement hourly activity heatmap computation in backend/app/services/analytics.py (hour_of_day, active_user_count, total_impressions, total_clicks, average_session_duration)
- [ ] T068 [US3] Implement daily activity trends computation in backend/app/services/analytics.py (date, daily_active_users, total_sessions, total_ad_interactions, average_sessions_per_user)
- [ ] T069 [US3] Implement per-user activity pattern computation in backend/app/services/analytics.py (preferred_hours, average_session_start_time, average_session_duration, most_active_day_of_week)
- [ ] T070 [US3] Create Celery task for materialized view refresh in backend/app/services/tasks.py (refreshes hourly_activity_heatmap every 15 minutes)
- [ ] T071 [US3] Create Celery task for user activity pattern computation in backend/app/services/tasks.py (computes patterns for active users)
- [ ] T072 [US3] Add query optimization for time-based analytics in backend/app/services/analytics.py (use materialized views for heatmaps, direct queries for user patterns)
- [ ] T073 [US3] Add logging for analytics operations in backend/app/services/analytics.py
- [ ] T074 [US3] Register analytics routes in backend/app/api/main.py

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work independently. System can compute and report time-based activity analytics including hourly heatmaps, daily trends, and user activity patterns.

---

## Phase 6: User Story 4 - User Information Reporting Dashboard (Priority: P2)

**Goal**: Provide comprehensive user information reports through API and dashboard for analyzing individual user profiles, ad interaction history, and behavioral patterns.

**Independent Test**: System can be tested by querying user reports for test users with known interaction histories and verifying all expected data fields are present, accurate, and properly aggregated.

### Implementation for User Story 4

- [ ] T075 [P] [US4] Implement user report generation service in backend/app/services/reporting.py (aggregates user profile, device history, location history, activity patterns, ad interactions, risk indicators)
- [ ] T076 [US4] Implement GET /reports/user/{user_id} endpoint in backend/app/api/routes/reports.py (returns comprehensive user information report)
- [ ] T077 [US4] Implement GET /reports/aggregate endpoint in backend/app/api/routes/reports.py (returns aggregate user reports with filtering)
- [ ] T078 [US4] Implement GET /reports/ad-interactions endpoint in backend/app/api/routes/reports.py (returns ad interaction performance reports)
- [ ] T079 [US4] Implement POST /reports/export endpoint in backend/app/api/routes/reports.py (exports reports in CSV/JSON format)
- [ ] T080 [US4] Implement risk scoring service in backend/app/services/risk_scoring.py (computes risk scores based on click velocity, session patterns, device consistency, IP reputation)
- [ ] T081 [US4] Add CRUD operations for RiskDecisionAudit in backend/app/crud.py (log risk decisions)
- [ ] T082 [US4] Implement user report aggregation logic in backend/app/services/reporting.py (combines UserProfile, UserDeviceHistory, UserLocationHistory, UserActivityPattern, AdInteraction, RiskDecisionAudit)
- [ ] T083 [US4] Implement aggregate report filtering logic in backend/app/services/reporting.py (filter by device_type, country, city, date_range)
- [ ] T084 [US4] Implement ad interaction report computation in backend/app/services/reporting.py (impressions per creative, CTR, completion rates, skip rates, user segment breakdowns)
- [ ] T085 [US4] Implement report export functionality in backend/app/services/reporting.py (CSV and JSON formats, configurable fields)
- [ ] T086 [US4] Add query optimization for user reports in backend/app/services/reporting.py (use indexes, batch queries, cache where appropriate)
- [ ] T087 [US4] Add query optimization for aggregate reports in backend/app/services/reporting.py (use materialized views, efficient filtering)
- [ ] T088 [US4] Implement data retention enforcement in backend/app/services/reporting.py (return available data within retention window, indicate date range limitations)
- [ ] T089 [US4] Add logging for reporting operations in backend/app/services/reporting.py
- [ ] T090 [US4] Register report routes in backend/app/api/main.py
- [ ] T091 [US4] Create frontend UserReport component in frontend/src/components/UserInfo/UserReport.tsx (displays user information report)
- [ ] T092 [US4] Create frontend TelemetryDashboard component in frontend/src/components/UserInfo/TelemetryDashboard.tsx (displays telemetry data)
- [ ] T093 [US4] Create frontend AnalyticsCharts component in frontend/src/components/UserInfo/AnalyticsCharts.tsx (displays time-based analytics)
- [ ] T094 [US4] Create frontend RiskIndicators component in frontend/src/components/UserInfo/RiskIndicators.tsx (displays risk indicators)
- [ ] T095 [US4] Create frontend route for userinfo dashboard in frontend/src/routes/userinfo/index.tsx
- [ ] T096 [US4] Create frontend route for individual user report in frontend/src/routes/userinfo/[userId].tsx
- [ ] T097 [US4] Generate frontend API client from OpenAPI spec in frontend/src/services/userinfoApi.ts
- [ ] T098 [US4] Add frontend integration with TanStack Query for data fetching in frontend/src/routes/userinfo/

**Checkpoint**: At this point, all user stories should be independently functional. System can generate comprehensive user reports, aggregate reports, ad interaction reports, and export functionality. Frontend dashboard provides operators with user information visualization.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T099 [P] Create Celery task for data movement to warm table in backend/app/services/tasks.py (moves 7-day-old data daily)
- [ ] T100 [P] Create Celery task for data movement to archive table in backend/app/services/tasks.py (moves 90-day-old data weekly)
- [ ] T101 [P] Create Celery task for data retention enforcement in backend/app/services/tasks.py (deletes data older than 13 months)
- [ ] T102 [P] Implement data freshness validation service in backend/app/services/data_freshness.py (validates hot metrics ≤5 min, aggregates ≤1 hour)
- [ ] T103 [P] Create Celery task for data freshness monitoring in backend/app/services/tasks.py (runs every 5 minutes, alerts on threshold violations)
- [ ] T104 [P] Implement ad delivery health monitoring service in backend/app/services/delivery_health.py (tracks impression-to-request ratios, fill rates, delivery latency)
- [ ] T105 [P] Create Celery task for delivery health monitoring in backend/app/services/tasks.py (runs every 5 minutes)
- [ ] T106 [P] Implement progressive risk response tiers in backend/app/services/risk_scoring.py (observation, rate_limit, shadow_ban, suspension based on risk score)
- [ ] T107 [P] Add audit trail logging for data access in backend/app/services/reporting.py (who, when, what, purpose - 13 month retention)
- [ ] T108 [P] Add privacy compliance handling in backend/app/services/telemetry.py (anonymize/hash PII where required by regional laws)
- [ ] T109 [P] Add transparency notices to frontend components in frontend/src/components/UserInfo/ (describe telemetry capture and usage)
- [ ] T110 Code cleanup and refactoring across all services
- [ ] T111 Performance optimization across all stories (query optimization, caching, indexing)
- [ ] T112 Security hardening (input validation, SQL injection prevention, rate limiting)
- [ ] T113 Run quickstart.md validation (verify all API endpoints work, test scenarios pass)
- [ ] T114 Documentation updates in specs/001-userinfo-report/ (update with implementation notes)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2)
- **Polish (Phase 7)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - Depends on UserProfile and UserSession from US1, but can be implemented in parallel
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - Depends on UserSession and AdInteraction from US1/US2, but can be implemented in parallel
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - Depends on all previous stories (UserProfile, UserSession, AdInteraction, UserActivityPattern), should be implemented after US1-US3

### Within Each User Story

- Models before services
- Services before endpoints
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Stories 1 and 2 can start in parallel (both P1)
- User Story 3 can start after US1/US2 models are complete
- User Story 4 should start after US1-US3 are complete
- All tests for a user story marked [P] can run in parallel
- Models within a story marked [P] can run in parallel
- Frontend components marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all models for User Story 1 together:
Task: "Create UserSession SQLModel in backend/app/models.py"
Task: "Create UserDeviceHistory SQLModel in backend/app/models.py"
Task: "Create UserLocationHistory SQLModel in backend/app/models.py"

# Launch all CRUD operations together:
Task: "Add CRUD operations for UserSession in backend/app/crud.py"
Task: "Add CRUD operations for UserDeviceHistory in backend/app/crud.py"
Task: "Add CRUD operations for UserLocationHistory in backend/app/crud.py"
```

---

## Parallel Example: User Story 2

```bash
# Launch service and endpoint implementation together (after models):
Task: "Implement ad interaction logging service in backend/app/services/interactions.py"
Task: "Implement POST /interactions endpoint in backend/app/api/routes/interactions.py"
Task: "Implement GET /interactions/{interaction_id} endpoint in backend/app/api/routes/interactions.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Comprehensive User Information Collection)
4. Complete Phase 4: User Story 2 (Ad Interaction Behavior Tracking)
5. **STOP and VALIDATE**: Test User Stories 1 & 2 independently
6. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (Basic telemetry)
3. Add User Story 2 → Test independently → Deploy/Demo (Ad tracking - MVP!)
4. Add User Story 3 → Test independently → Deploy/Demo (Time-based analytics)
5. Add User Story 4 → Test independently → Deploy/Demo (Full reporting)
6. Add Polish phase → Final production-ready system
7. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (telemetry collection)
   - Developer B: User Story 2 (ad interactions) - can start after UserProfile/UserSession models
3. After US1/US2 complete:
   - Developer A: User Story 3 (analytics)
   - Developer B: User Story 4 backend (reporting services)
   - Developer C: User Story 4 frontend (dashboard components)
4. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Database migrations must be run in order (T006-T015)
- Models must be created before services that use them
- Services must be created before endpoints that use them
- Frontend components depend on backend API endpoints being complete

