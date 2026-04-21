# IT-9.0 — Situation Rooms: Concept, Architecture, and Scope

## Overview

IT-9.0 defines the conceptual foundation, architectural positioning, and scope for Situation Rooms. This document anchors all subsequent IT-9 implementation steps.

---

## 1. Purpose of Situation Rooms

A **Situation Room** is a real-time operational intelligence dashboard for a workspace.

### 1.1. Real-Time Visibility

Provide a "live command center" showing:

- Current operational status
- Recent events
- Errors
- Pending actions
- Communication signals (Twilio/Resend today → Ghexit tomorrow)
- Jarvis agent activity
- System health

### 1.2. Operational Awareness

Surfacing:

- Tasks completed / failed
- Services degraded
- Repeated errors
- Slow handlers
- Failed event deliveries
- User activity spikes
- Suspicious behavior
- External provider outages (Twilio → Ghexit)

### 1.3. Intelligence Layer

Later in IT-10+, the Situation Room becomes the place where:

- Patterns are detected
- Alerts are triggered
- Predictions are shown
- Jarvis recommends actions
- Auto-fix behavior begins

### 1.4. Room Customization

Each workspace may have:

- One default room
- Additional custom rooms
- Specialized rooms (Billing Room, Support Room, AI Room, Provider Room)

---

## 2. Architectural Positioning

Situation Rooms sit on top of:

```
GEM (Global Event Mesh)
      |
      → Feed system
      → Event delivery system
      → Provider adapters
      → Event timeline storage
      → Event search/index filters

NEXUS analytics layer
      |
      → Situation Rooms (what we're building)
```

**Key relationship:**

- **GEM** = "what happened"
- **Situation Rooms** = "what does it mean right now"

So IT-9.0 formalizes:

- GEM as ground truth
- Situation Rooms as operational interpretation

---

## 3. Technical Scope Defined in IT-9.0

### 3.1. Inputs

Situation Rooms consume:

- GEM events
- Derived metrics from analytics
- Provider signals (Twilio/Resend → Ghexit)
- Jarvis internal logs (memory, timeline, journal)
- Delivery statuses
- Webhook failures
- Command performance stats
- Database latency (optional)
- External service health pings (later IT-17)

### 3.2. Outputs

Rooms produce:

- Live UI updates
- Alerts (later IT-11)
- Admin insights
- Trend visualizations
- Agent trigger conditions (IT-12)

### 3.3. Functional Requirements

**Real-time-ish updates**

- Polling or WebSockets (Later: Supabase Realtime? You have options).

**Multiple widget types**

- Event Feed
- Metric Card
- Error List
- Communication Log Widget
- Provider Health Widget
- Timeline Widget
- Delivery Failure Monitor
- Ghexit Communication Map (future)

**Room Layout Engine**

- Grid system to place widgets.

**Filters**

Room-level and widget-level filters:

- by event type
- by provider
- by severity
- by timeframe

**Expandable widgets**

- Future-ready for charts, AI explanations, predictions.

---

## 4. Security Model

Defined in IT-9.0:

- Rooms and widgets apply the workspace RLS model.
- Only members of a workspace can view its Situation Rooms.
- Cross-workspace access is impossible.
- Future enterprise mode: RBAC for widget/room access.

---

## 5. Provider Integration (Twilio → Ghexit)

Situation Rooms must abstract ALL providers behind a unified event interface.

In IT-9.0 we formally declare:

### Provider Normalization Protocol (PNP)

Every provider must produce normalized events with shape:

```
external.provider.<provider_name>.<event_type>
```

**This means:**

- Ghexit ≠ special
- Ghexit plugs into the same contract
- Replacing Twilio is trivial
- Widget filters do not change
- Dashboards continue working without modification

**This protocol is what ensures future Ghexit compatibility.**

---

## 6. Situation Rooms v0 → v3 Roadmap

IT-9.0 establishes the roadmap:

### v0 (IT-9.1 to IT-9.5)

- Basic rooms
- Basic widgets
- Event feed
- Error feed
- Metric cards
- Grid layout
- Polling-based refresh
- GEM-based data

### v1 (later IT-10+)

- Real-time streaming (WebSockets or Realtime)
- Trend charts
- Provider health analytics
- Ghexit communication dashboards
- Agent-triggered alerts

### v2

- Machine learning:
  - anomaly detection
  - drift detection
  - AI warnings
  - root-cause insights

### v3

- Fully autonomous NOC (Network Operations Center)
- Jarvis self-repair actions
- SLA enforcement
- Predictive analytics

---

## 7. IT-9.0 Acceptance Criteria

IT-9.0 is complete when:

### ✔ A. Situation Room Concept is defined

We now have a precise purpose and scope.

### ✔ B. Architecture is declared

- GEM → Situation Rooms pipeline
- Nexus analytics layer
- Widget-based UI supported by feeds

### ✔ C. Provider Interface formalized

Ghexit-ready normalization protocol defined.

### ✔ D. Security model established

- Workspace RLS
- Optional RBAC future

### ✔ E. Roadmap for expansion provided

v0 through v3 clarity.

---

## Result: IT-9.0 Complete

Now the entire IT-9 suite is correctly ordered:

1. **IT-9.0** — Concept, goals, architecture (THIS DOCUMENT)
2. **IT-9.1** — Default room creation
3. **IT-9.2** — Widget renderer system
4. **IT-9.3** — Room page + widget layout
5. **IT-9.4** — Metric providers
6. **IT-9.5** — Live mode + auto-refresh

---

## Implementation Status

- ✅ IT-9.0: Concept and architecture defined
- ✅ IT-9.1: Default room seeding implemented
- ✅ IT-9.2: Widget renderer system implemented
- ✅ IT-9.3: Room page with widget layout implemented
- ✅ IT-9.4: Metric providers implemented
- ✅ IT-9.5: Live mode with auto-refresh implemented
- ✅ Provider abstraction layer implemented (Ghexit-ready)

**IT-9 is now fully complete and production-ready.**

