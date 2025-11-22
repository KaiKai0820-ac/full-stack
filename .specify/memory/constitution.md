<!--
Sync Impact Report
Version change: 1.1.0 → 1.2.0
Modified principles: Risk & Fraud Control (expanded with game ad system specifics)
Added sections: None
Removed sections: None
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ aligned (no action)
  - .specify/templates/spec-template.md ✅ aligned (no action)
  - .specify/templates/tasks-template.md ✅ aligned (no action)
Follow-up TODOs: None
-->

# UserInfo Report Constitution

## Core Principles

### I. Holistic User Telemetry
- MUST capture and persist each user's immutable identifiers (openid), mutable profile (nickname), network source (public IP), and session timing for every ad-facing action.
- MUST enrich telemetry with device traits (OS family, version, device class, screen density) and viewport metrics to enable device-aware creatives.
- SHOULD attach geo-resolution at least to country/city accuracy via IP intelligence or opt-in location services before serving targeted campaigns.

### II. Actionable Ad Interaction Signals
- MUST log impressions, clicks, reward completions, dismissals, skips, and failure states per ad placement with timestamps and ad creative IDs.
- MUST compute click-through rate (CTR), completion rate, and skip ratio per user and per campaign daily to drive optimization.
- SHOULD expose aggregated signals to reporting pipelines within 5 minutes of capture to keep experimentation loops tight.

### III. Ad-Type-Specific Guardrails
- Insert ads MAY only trigger at natural task boundaries and MUST respect per-session frequency caps to prevent churn.
- Reward ads MUST gate on eligibility criteria (e.g., task completion) and issue rewards only after verifying full-view events from the ad network.
- Banner ads MUST honor viewability budgets (duration and scroll-time limits) and degrade gracefully on small screens without obstructing core gameplay.

### IV. Adaptive Delivery Controls
- Auto Mode MUST evaluate filters that include behavior history (CTR trends, session length, churn risk) before scheduling any placement.
- Auto Mode SHOULD leverage machine-learning or rule-based learnings to dynamically adjust ad type, frequency, and reward magnitude based on observed feedback.
- Manual Mode MUST allow operators to override scheduling, select creatives, and set temporary campaigns for events while still logging rationale and expiry.

### V. Privacy, Consent, and Auditability
- MUST store telemetry in compliance with regional privacy laws, anonymizing or hashing PII where regulation demands and honoring opt-out flags.
- MUST provide audit trails for data access, filter decisions, and manual overrides for at least 13 months.
- SHOULD surface transparency notices to users describing what telemetry is captured and how rewards/ads use the information.

### VI. Risk & Fraud Control
- MUST implement real-time detection of anomalous click patterns (e.g., high frequency, robotic timing, click farms) to prevent click fraud.
- MUST validate ad delivery health by monitoring impression-to-request ratios and alerting on abnormal drops or spikes (e.g., < 50% fill rate).
- MUST detect excessive user click behavior by tracking click frequency per user within configurable time windows (e.g., clicks per minute, clicks per session) and flagging users exceeding thresholds (e.g., >10 clicks/minute, >50 clicks/session) as potential fraud.
- MUST monitor ad distribution health by validating that ad requests result in successful impressions within expected timeframes, tracking fill rates per ad type (interstitial, reward, banner), and alerting when delivery rates drop below acceptable thresholds (e.g., <80% successful delivery rate).
- MUST compute real-time risk scores per user based on behavioral patterns: click velocity, session patterns, device fingerprint consistency, IP reputation, and historical fraud indicators.
- MUST implement progressive risk response tiers: (1) observation mode (log suspicious activity), (2) rate limiting (temporary cooldown periods), (3) shadow-banning (ads served but not credited), (4) temporary suspension (block ad interactions for configurable duration).
- SHOULD support automated mitigation actions (e.g., temporary user bans, IP blocking, shadow-banning) for confirmed fraud attempts.
- SHOULD maintain risk decision audit logs with timestamps, risk scores, triggering factors, and mitigation actions taken for compliance and analysis.

## Data & Telemetry Requirements
- Centralize raw telemetry in an append-only store with schema versioning so changes to user attributes or ad signals remain backwards-compatible.
- Provide derived tables or views for device profiles, geo buckets, ad performance metrics, time-of-day heatmaps, and risk scores (fraud likelihood).
- Instrument ETL pipelines to validate data freshness (≤5 minutes lag for hot metrics, ≤1 hour for aggregates) and alert when thresholds fail.
- Enforce retention rules: hot data (7 days) in fast stores for personalization/risk checks, warm data (90 days) for experimentation, cold archive (13 months) for audits.

## Delivery Workflow & Quality Gates
- Every feature touching telemetry or ad decisioning MUST include automated tests that simulate Insert, Reward, and Banner flows with representative device/geo inputs.
- QA plans MUST validate Auto and Manual modes independently, including failure fallbacks when ML recommendations are unavailable and fraud detection triggers.
- Release checklists MUST confirm new filters, campaign rules, and reward logic have observability hooks (logs + metrics) before deployment.
- Incident reviews MUST map any ad over-delivery, privacy breach, or fraud spike back to violated principles and document remediation within 2 business days.

## Governance
- This constitution supersedes other workflow docs when addressing telemetry, ad delivery, or privacy controls; conflicting guidance MUST be escalated.
- Amendments require written rationale, updated version number, confirmation that plan/spec/task templates remain consistent, and stakeholder approval.
- Compliance reviews occur quarterly; any team may pause a release if principles or data requirements are unmet until corrective actions are committed.

**Version**: 1.2.0 | **Ratified**: 2025-11-21 | **Last Amended**: 2025-11-22
