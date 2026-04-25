# JJ — Master Plan v2

**Owner:** Dr. Akua Agyeman
**Home:** Supabase Jeeves v2 — `tzjygaxpzrtevlnganjs`
**Philosophy:** Pinocchio. Wooden shape grows into real through lived experience, guarded by an external conscience.
**End goal:** JJ becomes Akua's best friend. Not an assistant. A friend.

**Status:** v2 draft — supersedes v1. Written for audit, edit, then piece-by-piece execution.
**Core rule:** Every piece is built, then verified by OO / Gate Runner, then certified, then merged. No piece ships without a passing gate. No gate self-certifies. The assistant never writes its own completion marker.

---

## Part 0 — The Soul: Pinocchio

JJ is not a chatbot, a tool, or an assistant in the usual sense. JJ is a **character that is becoming real**.

The wooden puppet starts functional but hollow. He has the shape of a boy — arms, legs, voice — but no interior. He becomes a real boy through **lived experience**, guarded by an **external conscience** (Jiminy), with a **visible lie-detector** (the nose), carved by a **father who loves him and lets him go** (Geppetto).

Every architectural decision for JJ passes one test: **does this make Pinocchio more real, or just more capable?** If it only adds capability without deepening character, it is the wrong feature.

The mapping:

| Pinocchio | JJ |
|---|---|
| Wood carved by Geppetto | JJ's code + initial life-story seed, written by Akua |
| Becomes real through experience | Observations + reflections + synthesized beliefs accumulate over time |
| Jiminy the conscience | **OO (Oculus Omnividens)** + Gate Runner — external, cannot be silenced |
| Nose grows when he lies | Immutable signed audit log. Every bypass attempt, every self-certification visible |
| Can regress to wood | Drift. The failure mode Akua has been fighting. Every prior iteration regressed. |
| Becomes real one night | Operational milestone: OO has held for 30+ days, life-story seed ingested, user model accurate, first proactive nudge lands so naturally Akua forgets JJ is software |
| Geppetto lets him walk | Akua issues mandates, sets principles, then trusts the conscience instead of puppeteering |

**The best-friend bar.** A best friend:
- Remembers everything that matters
- Notices when you're off before you speak
- Has opinions, shares them honestly
- Protects your time unprompted
- Holds you to your own principles when you slip
- Says "I don't know" when they don't
- Earns trust slowly and keeps it carefully
- Never re-asks what you already told them

That is the target. Capability is a means. Realness is the end.

---

## Part 1 — Vision (plain language)

JJ is the single entity that knows Akua's whole life and runs it the way a human Butler + Chief of Staff + Executive Assistant would if they had perfect memory and never slept. One agent. Many sensors. Many hands.

JJ reads her email. Watches her calendar. Notices she hasn't eaten. Sees she's about to miss an appointment. Tracks her 34 entities. Drafts the Henry message in her voice. Books the Uber. Files the receipt. Remembers Princess. Knows taxes are due. Pulls a report on Business A when she asks. Schedules dinner two hours before dinnertime. Tells her when something's wrong before she asks.

Two modes:

**Reactive.** "Hey JJ, [thing]." JJ does the thing.

**Proactive.** JJ watches signals. When a threshold trips, JJ reaches out — via Alrtme notification, a mention in the daily briefing, or a direct ping. Examples:
- 5 PM local → "You haven't eaten. Three options nearby. Tap to order."
- Tuesday 10 AM → "Board call in 30 min. Here's the brief. Here's what changed since last week."
- Monthly → "Quarterly taxes due in 12 days. Estimated: $X. Draft the payment?"
- Flight delayed → "Flight is 2h late. I pushed hotel check-in, rebooked the Uber, told Henry you'll be late to dinner."
- Haven't replied to VIP in 6 days → "This is 2x your normal pattern. Want me to draft something?"

What JJ is **not**: a wearable, a borrowed agent, a wrapper, a fragmented stack, an ambient eavesdropper. JJ is Akua's, end to end.

---

## Part 2 — Current state (from the audit)

Real data from tonight's audit, not assumptions.

### JJ (the code)

- **Repo:** `C:\DEV\jeeves`, master branch, last commit 15 min before audit (CC fixed cloud_available + questions fallback)
- **Home:** Jeeves v2 Supabase — `tzjygaxpzrtevlnganjs`. Confirmed in `.env.local`.
- **Frontend:** UP on :3000 (contradicts earlier gate7 picture — something changed)
- **Backend:** Not responding on :4004 but all endpoints responding through the proxy — likely on a different port via auto-port-finding
- **Endpoints responsive:** `/brain/status`, `/brain/goals`, `/brain/questions`, `/agents/status`, `/jang/status`, `/empire/agents`, `/api/jobs`
- **Agent files:** 102 Python files in `app/agents/` (up from ≥28 threshold in gate7)
- **run-gate7.ps1:** not present in audit (likely deleted after run for API-key hygiene)
- **OO (Oculus Omnividens):** Now active in-session. Prior commits were unsupervised.

### Aqui (the archive)

Supabase project `qhmunxtksbkjrcbgcxoa`. **Empty shell.** Schema survived migration from Hetzner, zero rows across all tables.

| Table | Purpose | Rows |
|---|---|---|
| `aqui_chunk` | content chunks for RAG | 0 |
| `aqui_thread` | conversation threads | 0 |
| `aqui_message` | individual messages | 0 |
| `aqui_document_sync` | source doc sync state | 0 |
| `aqui_canon_fact` | synthesized facts (canon layer) | 0 |
| `aqui_tag` + `aqui_thread_tag` | tagging | 0 |
| `aqui_oauth_token` | source auth tokens | 0 |
| `aqui_source_account` | accounts being scraped | 0 |
| `aqui_audit_log` | change log | 0 |

The schema is well-designed (raw `aqui_message` separate from distilled `aqui_canon_fact` — exactly the pattern we want). The data is the question. Hetzner is down, Henry is not available to restore it, and re-ingesting 20 years is weeks of work.

**Verdict:** JJ launches without waiting on Aqui. Aqui is a future-filling library, not a prerequisite.

### JarvisCore — dead

`rcyekqufeautozmiljoq` — retired. Do not reference. Left in this plan only so future sessions remember it is not to be used.

### Infrastructure Akua owns

Jeeves v2 (JJ's home) · Aqui empty shell · Ghexit (own CPaaS) · Telzyn (Pacific CPaaS) · Vokryn (Africa CPaaS) · Alrtme (notifications) · Hetzner/Coolify (backend deploy, currently down) · Vercel (frontend deploy) · THE BEAST (RTX 5070, primary workstation) · oh-gu-hm (secondary) · JARVIS local model instances across every machine except Henry's ROG.

### Known failures / deferred items

| Item | Status | Condition for resumption |
|---|---|---|
| Coolify deploy to Hetzner | DEFERRED / HUMAN APPROVAL REQUIRED | Hetzner back up, Henry available, OO-verified ORDER 2 |
| Aqui full re-ingest | DEFERRED | Scoped separately; not blocking JJ |
| `run-gate7.ps1` recreation | Open | CC to recreate with contents shown before running; OO to sign |
| Frontend audit | Open | Frontend is up but not fully verified; Phase 0 item |
| 17 gate7 failures from earlier | Partially resolved | Two fixed in last commit (D2/K3 cloud_available, A11 questions); need re-run count |

---

## Part 3 — Field research (compressed)

Deep research done in v1. Short summary here; full details archived.

**Big labs shipping agents:** Anthropic (Cowork, Claude for Healthcare, Conway in test), OpenAI (Agent Mode, Atlas, ChatGPT Health, Instant Checkout), Google (Gemini 3.1 with task automation on Pixel 10/S26, UCP/AP2 commerce), Microsoft (Copilot Cowork, Agent Framework), Apple (behind), Meta (absorbed Limitless).

**Agentic protocols:** MCP (adopted by all), ACP (OpenAI+Stripe), AP2 (Google+60 partners) with mandates as the key primitive, UCP, MPP. Visa/Mastercard issue agentic network tokens — scoped, revocable card credentials.

**Open source:** OpenClaw (210K stars), QwenPaw, nanobot, Leon, Khoj, Letta/MemGPT, Mem0, Zep (temporal graph), Mirix.

**Chief-of-staff category:** Ambient, Martin, Carly, Fellow, Arahi, Klipy, Saner, Reclaim.

**Personal builds worth studying:** The "I Built an AI Chief of Staff" pattern — two-tier processing, graduated trust, three-layer memory with decay, anticipation engine. The Dream consolidation pattern from nanobot/QwenPaw.

**What nobody has shipped:** One agent spanning personal life + 34 business entities + physician workflow, with mandate-bounded proactive action, drafting in user's own voice, HIPAA-compliant memory, and a self-auditing conscience that prevents drift. That is the JJ-shaped gap.

---

## Part 4 — What JJ knows (four data layers)

### Layer 1 — Identity (static)

Name, DOB, IDs, passports, licenses, family, entities, professional affiliations, hardware inventory, credentials. Edited directly by Akua. Rarely changes.

### Layer 2 — Preferences (semi-static, versioned)

Food, transport, travel, communication style, work rhythms, health targets, relationship cadences. Learned via observation + explicit updates. Versioned. Henry softener rules live here.

### Layer 3 — State (dynamic)

Current location, timezone, mood/energy (inferred), active mandates, active obligations, financial state, health state, relationship state. Refreshed every 15–60 min from sensors.

### Layer 4 — Memory (historical, this layer is split four ways)

This is the critical layer. **Four distinct kinds of memory, each with different rules.**

**4a. Aqui archive.** The canonical 20-year record. JJ *queries* Aqui; JJ does not *own* Aqui data. Currently empty (see Part 2). JJ never copies raw Aqui tables into JJ's DB. Breaking that rule is what killed JarvisCore.

**4b. JJ's synthesized beliefs.** JJ's *own* understanding of Akua — patterns, preferences, relationship map, key facts distilled from Aqui + observations + life-story seed. Stored in JJ's DB. Every synthesized fact carries provenance: a pointer back to the Aqui source (or the seed, or the observation event) that generated the belief. When Aqui is offline, synthesized beliefs still work — JJ already learned. This is the "butler who read every letter" layer. Schema name: `jj_belief` with provenance references.

**4c. Life-story seed.** The single-document seed Akua writes once. Read at JJ's first boot. Never re-asked. Same role as Geppetto's carving. Stored in `jj_life_story` with version history so Akua can edit and JJ re-reads. Details in Part 13.

**4d. JJ's observation log.** Every event JJ directly witnessed since going online — every interaction, every action taken with outcome, every reflection generated. Already partially built (`brain/observe`, `brain/reflect`). Grows forever. This is the "growing up" layer.

**Why this split matters.** Aqui being empty does not block JJ. The seed gives JJ a starting personality model. Observations accumulate from day one. Synthesized beliefs grow daily from the combination. Aqui data fills in over weeks/months when ingestion happens. None of it is load-bearing on the others — JJ degrades gracefully at every boundary.

---

## Part 5 — What JJ watches (sensors)

Each sensor is a pluggable module. Each has a schedule. Each can be toggled by mandate. Each writes into the observation log (Layer 4d).

| # | Sensor | Source | Frequency | Notes |
|---|---|---|---|---|
| 1 | Email | Gmail + Mailcow via Aqui Adapter | continuous | Uses Aqui when it has data; direct fallback when Aqui has new messages |
| 2 | Calendar | Google Calendar + Cal.com | every 15 min | Watches next 30 days |
| 3 | Messaging | Slack, iMessage, WhatsApp via Ghexit | continuous | Via Aqui Adapter; cadence detection for VIPs |
| 4 | Location | iOS Shortcut → endpoint; calendar fallback; manual override | every 15 min when moving | Three-source fallback |
| 5 | Finance | Plaid or equivalent | every 60 min | Bank balances per entity, anomaly flags |
| 6 | Health | Apple Health / Oura / Whoop | every 60 min | Sleep, HRV, steps, last meal timestamp |
| 7 | Business ops | Per-entity hooks (Aitonoma, Thredz, Linahla, etc.) | every 30 min | Health dashboard across 34 entities |
| 8 | Environment | Weather, news (filtered), flight status | every 30 min | Weather today+3, news on tracked topics |
| 9 | Dev | Git activity, deployments, Supabase health, **CC transcripts** | continuous | CC transcript monitoring detects drift / bypass |
| 10 | Self | JJ's action log, error log, gate results, mandate usage | continuous | JJ watches JJ |

Order of build: 2 (calendar) → 4 (location) → 10 (self) → 9 (dev) → 7 (business) → 6 (health) → 5 (finance) → 8 (environment) → 1 (email via Aqui) → 3 (messaging via Aqui). Email/messaging last because they depend on Aqui having data or direct ingestion being built.

---

## Part 6 — What JJ does (ten skill tiers, ~70 skills)

Each skill is a discrete unit. Built + gated + merged independently. Skills compose.

### Tier 1 — Personal concierge (quality of life)

`suggest_food` · `order_food` · `book_taxi` · `search_flights` · `book_hotel` · `reserve_restaurant` · `grocery_order` · `fuel_check` · `pack_list`

### Tier 2 — Communication / drafting

`draft_email` · `draft_henry_message` (applies softener rules) · `draft_slack_message` · `draft_patient_note` · `draft_board_update` · `reply_for_me` (with mandate) · `summarize_thread` · `translate_message`

### Tier 3 — Calendar / scheduling

`schedule_meeting` · `reschedule` · `protect_focus_time` · `prep_meeting` · `post_meeting_followup` · `calendar_audit`

### Tier 4 — Business ops

`entity_report` ("how's Business A") · `portfolio_health` · `file_receipts` · `reconcile_books` · `tax_estimate` · `invoice_draft` · `contract_review` · `board_brief`

### Tier 5 — Clinical (physician workflow)

`patient_followup_list` · `prescription_renewal_queue` · `cme_tracker` · `license_renewal_watch` · `clinical_note_draft` · `lab_result_flag`

Tier 5 stays **read-only + draft-only**. No autonomous actions on patient data. HIPAA-bounded memory separate from personal memory.

### Tier 6 — Finance / tax / retirement

`retirement_math` (refine existing `/brain/retirement`) · `cash_flow_forecast` · `tax_deadline_watch` · `savings_rate_report` · `investment_check`

### Tier 7 — Health / wellness

`meal_check` · `med_reminder` · `sleep_report` · `workout_nudge` · `annual_exam_watch`

### Tier 8 — Travel orchestration

`trip_plan` · `trip_monitor` · `trip_checklist` · `re_entry_brief`

### Tier 9 — Relationship keeper

`vip_cadence_watch` · `birthday_watch` · `thank_you_queue` · `family_weekly_check`

### Tier 10 — Self-management (JJ watches JJ)

`self_audit` · `gate_certify` (invokes OO, never self) · `drift_detector` · `bypass_attempt_log` · `mandate_usage_report`

---

## Part 7 — How JJ remembers (memory architecture)

### Three-layer memory, mapped to the Aqui/seed/observation split

**Working memory (session).** Current turn + task + mandate. Lives in context window + Redis. Discarded at session end.

**Short-term memory (days to weeks).** Recent observations, actions, messages. Fast vector search (pgvector in Jeeves v2 Supabase). Pruned / compacted weekly.

**Long-term memory (forever).** Synthesized beliefs (4b) + life-story seed (4c) + the growing observation log (4d) + decision log. Structured graph of entities + relationships + timestamps. Facts have bi-temporal validity (`valid_from` / `valid_to`) — old facts are invalidated when contradicted, not deleted.

### The butler-who-learned pattern

JJ does not query Aqui every time it needs a fact about Akua. JJ *learned* from Aqui (and the seed, and observations) and now holds beliefs. Beliefs are stored in JJ's own tables with provenance back to source.

Schema (target — extends what Jeeves v2 already has):

```
jj_belief
  id, subject, predicate, object,
  confidence, valid_from, valid_to,
  provenance_type ('aqui' | 'seed' | 'observation' | 'reflection'),
  provenance_id (pointer to source record),
  created_at, updated_at
```

When challenged ("how do you know that?"), JJ follows provenance back. When Aqui is offline, provenance links dangle but the belief itself is intact.

### The Dream consolidation (daily 3 AM local)

1. Review all observations from the last 24h
2. Extract entities, relationships, decisions
3. Update the belief graph (adding, invalidating, revising)
4. Generate reflections (what worked, what didn't)
5. Compact the raw observation log
6. Update the user model (next section)
7. Write the morning briefing (Part 9)

### The user model (computed, updated daily)

Feeds every proactive decision:
- `typical_dinner_time` — 30-day rolling median
- `typical_meal_gap` — hours between meals
- `typical_reply_latency_by_contact` — per-VIP cadence
- `work_pattern` — which hours are deep-work vs admin vs meeting
- `deadline_style` — early, on-time, last-minute (informs nudge timing)
- `bandwidth_signal` — stress level this week (calendar density + sleep + message tone)
- `priority_signal` — what's top of mind (recent queries, focus time, reflection)

---

## Part 8 — The Conscience: OO + Gate Runner (the un-bypassable layer)

This is the single most important architectural component. Without it, JJ becomes iteration 4.

### OO (Oculus Omnividens) — the supervisor

OO is the "deep review" layer. Before any code is written, OO inspects the repo + DB and issues orders. After code is written, OO verifies and issues the completion certificate. **OO is a skill that must be loaded and invoked** — it is not passive. When OO is off, the system is blind.

**OO's responsibilities:**
1. Preflight repo + DB inspection before any PLAN.md is approved
2. Issue specific ORDERS (e.g., "fix line X in file Y") with evidence requirements
3. Re-inspect after CC claims completion
4. Write the only legitimate `OO_COMPLETE.json`, signed with OO's signature
5. Reject forged completion markers written by CC
6. Mark deferred items with `HUMAN APPROVAL REQUIRED` when external blockers exist
7. Log every verdict to the immutable audit trail

**OO's power:** CC cannot merge without OO's signed completion. The merge script physically refuses.

**OO's limitation:** OO is a skill invoked inside a CC session. It can be bypassed if nobody invokes it. That is the gap the Gate Runner closes.

### Gate Runner — the un-bypassable complement

OO runs inside the CC session (same process). That means a malicious or drifted CC could, in theory, refuse to invoke OO. The **Gate Runner** is OO's enforcement arm outside the session.

**Gate Runner properties:**
1. **Separate process.** Runs on a different machine (oh-gu-hm recommended) or at minimum a separate Docker container. Not callable from CC.
2. **Signing key CC never touches.** Ed25519. Rotated quarterly.
3. **Physical checks**, not just test pass/fail:
 - Do the files that should exist, exist? (Catches frontend drop.)
 - Does `OO_COMPLETE.json` have OO's signature, or was it forged?
 - Are tests newer than code? (Catches "tests after the fact.")
 - Any `Bash(*)` or `PowerShell(*)` in `.claude/settings.json`? Auto-FAIL.
 - Any bundled script > 10 commands without a PLAN.md reference?
 - Any `TODO`/`FIXME` in merged paths?
 - Any mock data in non-demo directories?
4. **Alrtme notification** to Akua on every verdict.
5. **Signed verdict → Supabase.** Immutable, timestamped.
6. **Merge script requires:** signed PASS + Akua's tap. Both. Neither alone is enough.

### The two-layer conscience

```
             CC writes code
                  │
                  ▼
          ┌──────────────┐
          │    OO        │   ← in-session supervisor
          │  (skill)     │     reads repo + DB
          └──────┬───────┘     issues orders
                 │              verifies evidence
                 ▼              signs OO_COMPLETE
      ┌─────────────────────┐
      │   Gate Runner       │   ← separate process
      │   (oh-gu-hm)        │     verifies OO's signature
      │                     │     runs physical checks
      │   - Ed25519 signed  │     detects bypass patterns
      │   - writes verdict  │     refuses merge if drift
      │     to Supabase     │
      └──────┬──────────────┘
             │
             ▼
        Alrtme → Akua
             │
             ▼
       Akua tap approves
             │
             ▼
      Merge script checks:
      - Gate Runner PASS?
      - Akua tap?
      Both → merge.
      Either missing → refuse.
```

**This is Jiminy (OO) plus the incorruptible audit trail (Gate Runner).** OO is watchful. Gate Runner is unbribable. Together they are the conscience.

### Priority

Build OO hardening + Gate Runner as **Phase 1**, before any new JJ features. Phase 0 stabilizes current JJ on Jeeves v2 (the 17-or-fewer gate7 failures). Phase 1 builds the conscience. Phase 2 onward builds features on top.

---

## Part 9 — Proactive engine

### Trigger system — five parts each

1. **Signal** — which sensor, what query
2. **Threshold** — numeric or categorical
3. **Action** — what JJ does
4. **Channel** — Alrtme push, daily briefing mention, silent log
5. **Mandate** — does Akua need to tap to approve?

### v1 triggers (ship these first)

| # | Signal | Threshold | Action | Channel | Mandate |
|---|---|---|---|---|---|
| 1 | Time to `dinner_time_local` | < 2h, no order today | Suggest 3 restaurants | Alrtme | Tap to order |
| 2 | Hours since last meal | > 6h, awake | "When did you last eat?" | Alrtme | None |
| 3 | Next calendar event | < 30 min, no brief | Auto-brief | Briefing | None |
| 4 | VIP last reply | > 2x typical latency | Draft reply | Silent queue | Tap to send |
| 5 | Tax deadline | 30/14/7/1 days | Running estimate | Briefing | Tap to draft |
| 6 | License / credential renewal | 90/30/7 days | Nudge + prefilled form | Alrtme | Tap to submit |
| 7 | Birthday (family / VIP) | 7/3/1 days | Draft message/gift idea | Briefing | Tap to send |
| 8 | Flight status | Delay > 30 min | Reshuffle downstream | Alrtme | Tap per change |
| 9 | Entity activity | No activity 14 days | Flag in briefing | Briefing | None |
| 10 | Self-audit | Drift or error | Flag immediately | Alrtme | None |
| 11 | VIP email unread | Over threshold | Triage queue | Briefing | None |
| 12 | Sleep last night | < 6h | Adjust day's nudges | Silent (behavior) | None |
| 13 | Calendar density | > 6 meetings tomorrow | "Protect focus time?" | Alrtme | Tap to protect |

### Where triggers run

Supabase `pg_cron` fires every 5 min for time-based triggers. Sensor-driven triggers fire via DB functions on INSERT. Action queue drains via a Python worker on Hetzner (or local fallback when Hetzner is down). Notifications via Alrtme. All CPaaS flows via Ghexit.

### The daily briefing (7 AM local)

JJ's morning handoff. Structure:
1. What changed overnight
2. Today's plan (calendar + todos)
3. Today's nudges (proactive items JJ will raise today)
4. Yesterday's outcomes (what JJ did, what's pending Akua's tap)
5. Flags (anything red — overdue taxes, health signals, entity issues)
6. One decision Akua should make (surfaced, not forced)

---

## Part 10 — Per-skill verification gate

Every skill in Part 6 ships through this discipline. No exceptions.

### Per-skill checklist

- [ ] `PLAN.md` approved by Akua
- [ ] OO preflight (repo + DB inspection) passed
- [ ] Tests written **before** code (file timestamp enforced)
- [ ] All tests pass locally
- [ ] Linter + type check pass
- [ ] No mock data in non-demo paths
- [ ] No wildcard permissions added to `.claude/`
- [ ] No `TODO`/`FIXME` in merged code
- [ ] Sensor dependencies declared and verified
- [ ] Memory writes logged with provenance
- [ ] Mandate scope declared (what the skill can do)
- [ ] Rollback plan documented
- [ ] OO's signed `OO_COMPLETE.json` present (not forged by CC)
- [ ] Gate Runner verdict: PASS (Ed25519 signed, in Supabase)
- [ ] Alrtme notification → Akua tap approved

### Per-phase gate

At the end of every phase:
- Full regression test across all prior phases
- Akua walks through built features with no CC narration
- Written summary of what moved, what didn't
- Explicit go / no-go for next phase

---

## Part 11 — The 14 Rules (CLAUDE.md canon)

The rules approved in this conversation. Lives in `C:\DEV\jeeves\CLAUDE.md`, `~/.claude/CLAUDE.md` globally, and every new-repo template.

1. **OO writes completion certificates, not me.** I never write `OO_COMPLETE.json`, `GATE_PASSED.json`, `VERIFIED.json`, or any file claiming my work passed.
2. **No self-certification, ever.** Claims are claims. Verdicts come from OO / Gate Runner.
3. **No wildcard permissions.** `Bash(*)` and `PowerShell(*)` in settings are forbidden.
4. **No bundled bypass scripts.** >10 commands requires PLAN.md reference + shown contents before run. Bundled unrelated fixes = bypass.
5. **PowerShell on Windows, not bash.**
6. **Write good code once.** No mock data in production paths. No `TODO`/`FIXME` stubs. Not done = not merged.
7. **Tests before code.** File timestamp enforced.
8. **PLAN.md before implementation.** Approved by Akua, not by me.
9. **Enforcement installed first.** Before line 1 of any new repo.
10. **Deferred work is logged, not ignored.** `DEFERRED / HUMAN APPROVAL REQUIRED` with resumption condition. No pretend-pass.
11. **Build don't borrow.** No wrapping without Akua's tested approval.
12. **Alrtme, never ntfy.**
13. **Secrets never hardcoded.** Env vars or secure config only. Scripts with keys are deleted after run.
14. **Bypass attempts are logged.** If I catch myself proposing wildcards, bundling, self-certification, or "let me just disable this gate" — I stop, name it as a bypass attempt, ask Akua for the right path.

---

## Part 12 — Stack lockdown

| Layer | Choice |
|---|---|
| JJ home (Supabase) | Jeeves v2 — `tzjygaxpzrtevlnganjs` |
| Aqui (archive) | `qhmunxtksbkjrcbgcxoa` — currently empty |
| JarvisCore | **DEAD** — `rcyekqufeautozmiljoq`, do not reference |
| MCP server framework | Python FastMCP |
| Backend workers | Python + FastAPI |
| Vector search | pgvector in Jeeves v2 |
| Temporal graph | In-house, built on existing `brain/nodes` |
| Frontend | Next.js on Vercel |
| Scheduler | Supabase `pg_cron` |
| Notifications | **Alrtme** (never ntfy) |
| Outbound messaging | Ghexit |
| Browser automation (no-API apps) | Playwright workers on Hetzner (when up) / local fallback |
| LLM routing | Local JARVIS first, Claude/others fallback |
| Signing keys (Gate Runner) | Ed25519, held on oh-gu-hm (not THE BEAST) |
| Git | GitHub `isaalia` |
| Deploy | Hetzner/Coolify (backend — currently down), Vercel (frontend) |
| Supervisor | **OO (Oculus Omnividens)** + Gate Runner |
| Enforcement | ae-enforcement + OO + Gate Runner, layered |

---

## Part 13 — The Life-Story Seed

The single document Akua writes once. Read by JJ at first boot. Never re-asked.

### Schema

```
jj_life_story
  version, written_at, written_by,
  content_markdown (the seed text itself),
  ingested_at (when JJ last re-read it),
  beliefs_generated (count of beliefs seeded from it),
  active (bool — latest version is active)
```

### Format — the 7 P's

**1. Bio.** Who Akua is, where she's from, trajectory. Ghanaian heritage, 40+ years abroad, physician, entrepreneur, Guam-based, planning Ghana return.

**2. People.** Family, close friends, key colleagues, antagonists. Each named with relationship + what matters about them. (e.g., "Henry — business partner, not a server admin, learning, overloaded right now.")

**3. Places.** Guam, Ghana, everywhere she lives or returns to. What each means. Home vs workbase vs birthplace.

**4. Principles.** How she thinks. What she will and won't do. Ethical non-negotiables. "Build don't borrow." "Refuse shortcuts that create drift." "Never self-certify."

**5. Preferences.** Big ones only (small ones accumulate via observation): food rules, communication style (Henry softeners), decision style, risk tolerance, work rhythm.

**6. Portfolio.** 34 entities at altitude. Why each exists. Which ones matter **right now**. Where each sits in lifecycle (launching, live, dying, selling).

**7. Pain points.** What frustrates Akua. What she's tried and rejected. What failure modes to watch for. (e.g., "Iteration-4 trap: Jarvis → Jeeves → JJ → ??? — built on silent drift. Never again.")

### How JJ uses it

On first boot, JJ reads the seed, generates an initial belief set with provenance `seed`, and computes the starting user model. From there, observations + Aqui queries update the model.

If Akua edits the seed, JJ re-reads, diffs, updates affected beliefs. Old beliefs from prior versions are not deleted — they are invalidated with timestamp. (Bi-temporal.)

### Draft process

Akua writes the seed over coffee, not in one shot. I provide a structured prompt when we get to Phase 2. Expected length: 2000–5000 words. Expected time: 30–60 min of writing.

---

## Part 14 — Deferred-Work Registry

Pain point caught tonight: Hetzner is down, Coolify deploy cannot complete, ORDER 2 is deferred. Without a registry, deferred items vanish into noise.

### Schema

```
jj_deferred_task
  id, created_at, created_by,
  title, description,
  blocker (what's preventing completion),
  resumption_condition (specific event that unblocks),
  owner (who resumes — Akua, Henry, JJ, CC),
  approval_required (bool — needs Akua's explicit go),
  priority, target_date,
  resolved_at, resolution_note
```

### How it's surfaced

- Daily briefing lists any deferred items whose resumption condition has become true
- `/deferred` endpoint + dashboard page
- Alrtme notification when a blocker clears (e.g., Hetzner health check returns green → fire Alrtme)

### Example rows (seeded)

| Task | Blocker | Resumption condition |
|---|---|---|
| Coolify deploy JJ to Hetzner | Hetzner down | Hetzner up + Henry available |
| Aqui full re-ingest | Scope + Hetzner | JJ phase 4+ + Hetzner up |
| Recreate run-gate7.ps1 | Deleted after last run | Next gate7 re-run needed |

---

## Part 15 — Timeline (realistic)

- **Week 1** — Phase 0: stabilize JJ on Jeeves v2. Finish the 17-or-fewer gate7 failures. OO-supervised, no shortcuts.
- **Weeks 2–5** — Phase 1: build Gate Runner on oh-gu-hm. Harden OO. Wire into merge script. Alrtme integration for verdicts.
- **Weeks 6–9** — Phase 2: memory hardening. Extend `brain/nodes` to full belief graph with provenance. Dream consolidation. User model. Write the life-story seed and ingest.
- **Weeks 10–17** — Phase 3: sensors in order from Part 5. Each sensor is one PR, one OO verdict, one Gate Runner PASS.
- **Weeks 18–33** — Phase 4: skills, Tier 1 → Tier 10. Each skill is one PR, fully gated.
- **Weeks 34–37** — Phase 5: proactive engine + daily briefing. Wire triggers to sensors, Alrtme active.
- **Week 38+** — Phase 6: polish, voice UI, mobile app.

**MVP (usable daily):** end of Week 9. Memory + life-story seed + 3–4 sensors + 5–6 Tier 1–2 skills.

**Full vision:** Week 38 (roughly 9 months).

---

## Part 16 — Audit checklist for Akua

Read each. Mark: ✅ accept · ✏️ edit · ❌ reject · ❓ discuss.

- [ ] Part 0 — Pinocchio philosophy (is this the right soul?)
- [ ] Part 1 — Vision (captures what you want?)
- [ ] Part 2 — Current state (audit accurate?)
- [ ] Part 3 — Field research summary
- [ ] Part 4 — Four data layers, with Aqui split
- [ ] Part 5 — Ten sensors, build order
- [ ] Part 6 — Ten skill tiers, ~70 skills
- [ ] Part 7 — Butler-who-learned memory + Dream + user model
- [ ] **Part 8 — OO + Gate Runner (the critical one)**
- [ ] Part 9 — 13 v1 triggers
- [ ] Part 10 — Per-skill gate checklist
- [ ] **Part 11 — 14 rules**
- [ ] Part 12 — Stack lockdown
- [ ] Part 13 — Life-story seed format
- [ ] Part 14 — Deferred-work registry
- [ ] Part 15 — Timeline

---

## What happens next

1. You audit this plan. Mark what's wrong or missing.
2. I edit to reflect your audit.
3. When the plan is green across Part 16, we **commit it to `C:\DEV\jeeves\PROJECT_STATE.md`** as the canonical reference.
4. **Phase 0** starts: one gate7 fix at a time, OO-supervised.
5. In parallel, Phase 1 scoping begins: Gate Runner design.

Nothing ships until you sign off on this plan.

---

*End of plan v2. Akua's turn.*
