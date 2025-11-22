# Implementation Plan: UserInfo Report

**Branch**: `001-userinfo-report` | **Date**: 2025-11-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-userinfo-report/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

The UserInfo Report feature enables comprehensive user telemetry collection, ad interaction tracking, time-based analytics, and reporting capabilities. This feature implements the foundational data layer for user profiling, ad targeting, and analytics as specified in the UserInfo Report Constitution. The implementation will extend the existing FastAPI backend with new data models, services, and API endpoints, while providing a React frontend dashboard for operators to view and analyze user information reports.

## Technical Context

**Language/Version**: Python >=3.10,<4.0 (backend), TypeScript 5.2+ (frontend)  
**Primary Dependencies**: FastAPI, SQLModel, Pydantic, PostgreSQL (backend), React, TanStack Router, TanStack Query, Chakra UI (frontend)  
**Storage**: PostgreSQL (primary database), NEEDS CLARIFICATION (hot/warm/cold data tiering strategy)  
**Testing**: pytest (backend), Playwright (frontend E2E)  
**Target Platform**: Linux server (backend), Web browsers (frontend)  
**Project Type**: web (backend + frontend)  
**Performance Goals**: 
- 10,000+ concurrent user sessions (SC-009)
- Hot metrics available within 5 minutes (SC-008)
- User reports generated within 2 seconds (SC-006)
- Aggregate reports within 5 seconds for 90-day ranges (SC-007)
- 100% of ad interaction events logged within 1 second (SC-003)
**Constraints**: 
- Data retention: hot (7 days), warm (90 days), cold archive (13 months) (FR-027)
- Data freshness: hot metrics ≤5 minutes, aggregates ≤1 hour (FR-028)
- Privacy compliance: regional privacy laws, opt-out handling (FR-029, FR-030)
- Audit trails: 13-month retention (FR-032)
**Scale/Scope**: 
- 10,000+ concurrent sessions
- Multiple ad types (interstitial, reward, banner)
- Real-time event logging and batch aggregation
- Multi-tier data storage architecture

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Holistic User Telemetry ✅
- **Requirement**: Capture immutable identifiers (openid), mutable profile (nickname), network source (IP), session timing
- **Status**: ✅ Covered by FR-001, FR-002, FR-003, FR-004
- **Requirement**: Enrich with device traits (OS, version, device class, screen density) and viewport metrics
- **Status**: ✅ Covered by FR-005, FR-006
- **Requirement**: Geo-resolution to country/city accuracy via IP intelligence or opt-in location
- **Status**: ✅ Covered by FR-007, FR-008

### Principle II: Actionable Ad Interaction Signals ✅
- **Requirement**: Log impressions, clicks, completions, dismissals, skips, failures with timestamps and ad creative IDs
- **Status**: ✅ Covered by FR-010 through FR-015
- **Requirement**: Compute CTR, completion rate, skip ratio per user and per campaign daily
- **Status**: ✅ Covered by FR-016, FR-017
- **Requirement**: Expose aggregated signals to reporting pipelines within 5 minutes
- **Status**: ✅ Covered by FR-018, SC-005

### Principle V: Privacy, Consent, and Auditability ✅
- **Requirement**: Store telemetry in compliance with regional privacy laws, anonymize/hash PII where required
- **Status**: ✅ Covered by FR-029
- **Requirement**: Honor opt-out flags for location tracking
- **Status**: ✅ Covered by FR-030
- **Requirement**: Provide audit trails for data access (who, when, what, purpose) for 13 months
- **Status**: ✅ Covered by FR-031, FR-032
- **Requirement**: Surface transparency notices to users
- **Status**: ✅ Covered by FR-033

### Principle VI: Risk & Fraud Control ⚠️ NEEDS CLARIFICATION
- **Requirement**: Real-time detection of anomalous click patterns, click farms
- **Status**: ⚠️ Not explicitly covered in spec - NEEDS CLARIFICATION for implementation approach
- **Requirement**: Validate ad delivery health (impression-to-request ratios, fill rates)
- **Status**: ⚠️ Not explicitly covered in spec - NEEDS CLARIFICATION for implementation approach
- **Requirement**: Detect excessive user click behavior (clicks per minute, per session)
- **Status**: ⚠️ Not explicitly covered in spec - NEEDS CLARIFICATION for implementation approach
- **Requirement**: Compute real-time risk scores per user
- **Status**: ⚠️ Mentioned in FR-023 (risk score in user reports) but implementation approach NEEDS CLARIFICATION
- **Requirement**: Progressive risk response tiers (observation, rate limiting, shadow-banning, suspension)
- **Status**: ⚠️ Not explicitly covered in spec - NEEDS CLARIFICATION for implementation approach

### Data & Telemetry Requirements ⚠️ NEEDS CLARIFICATION
- **Requirement**: Centralize raw telemetry in append-only store with schema versioning
- **Status**: ⚠️ NEEDS CLARIFICATION for storage architecture (append-only vs. relational)
- **Requirement**: Derived tables/views for device profiles, geo buckets, metrics, heatmaps, risk scores
- **Status**: ⚠️ NEEDS CLARIFICATION for materialized views vs. real-time computation strategy
- **Requirement**: ETL pipelines with data freshness validation and alerting
- **Status**: ⚠️ NEEDS CLARIFICATION for ETL tooling and monitoring approach
- **Requirement**: Multi-tier retention (hot 7 days, warm 90 days, cold 13 months)
- **Status**: ⚠️ NEEDS CLARIFICATION for data tiering implementation (separate databases, partitioning, archiving)

**Gate Status**: ⚠️ **CONDITIONAL PASS** - Core telemetry and interaction tracking requirements are fully specified. Risk/fraud control and data tiering architecture need clarification before Phase 1 design.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models.py              # Existing models (User, Item) + new UserInfo models
│   ├── api/
│   │   ├── routes/
│   │   │   ├── userinfo.py    # New: UserInfo report endpoints
│   │   │   ├── telemetry.py   # New: Telemetry collection endpoints
│   │   │   └── analytics.py   # New: Analytics and aggregation endpoints
│   │   └── main.py
│   ├── services/
│   │   ├── telemetry.py       # New: Telemetry collection service
│   │   ├── geolocation.py     # New: IP geolocation enrichment service
│   │   ├── analytics.py       # New: Time-based analytics computation
│   │   ├── reporting.py       # New: Report generation service
│   │   └── risk_scoring.py    # New: Risk/fraud detection service
│   ├── crud.py                # Existing CRUD + new UserInfo CRUD operations
│   └── core/
│       ├── config.py          # Existing config + new UserInfo settings
│       └── db.py
└── tests/
    ├── api/
    │   └── routes/
    │       ├── test_userinfo.py
    │       ├── test_telemetry.py
    │       └── test_analytics.py
    └── services/
        ├── test_telemetry.py
        ├── test_geolocation.py
        └── test_risk_scoring.py

frontend/
├── src/
│   ├── components/
│   │   └── UserInfo/
│   │       ├── UserReport.tsx
│   │       ├── TelemetryDashboard.tsx
│   │       ├── AnalyticsCharts.tsx
│   │       └── RiskIndicators.tsx
│   ├── routes/
│   │   └── userinfo/
│   │       ├── index.tsx       # UserInfo dashboard
│   │       └── [userId].tsx    # Individual user report
│   └── services/
│       └── userinfoApi.ts     # Generated from OpenAPI
└── tests/
    └── userinfo.spec.ts       # E2E tests for UserInfo features
```

**Structure Decision**: Web application structure (backend + frontend) is already established. New UserInfo Report feature will extend existing backend API routes and services, and add new frontend components for the reporting dashboard. All new code follows existing patterns: SQLModel for data models, FastAPI routes, Pydantic schemas, React components with TanStack Router.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
