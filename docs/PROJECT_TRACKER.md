# Faculty Workload Planning Agent — Project Tracker

> Living document for tracking completed and pending work.  
> **Last updated:** 2026-06-25 (multi-batch course catalog, lecture halls, PEC/SEC rules)

---

## Build order — what first?

**Faculty list UI is optional early.** It is a quick visual win, but **not required** for the optimizer.

**Master data must exist before allocation.** The engine needs:

```
Faculty (who can teach)          ✅ done
    +
Subjects / courses (what to teach, per semester)   ✅ done
    +
Classrooms & laboratories (where)                  ✅ done
    +
Time slots / timetable grid (when)               ✅ daily periods seeded
    +
Policies (AICTE hours, lab limits, fairness)      ✅ seeded
    ↓
Optimization run
```

| Approach | When to use |
|----------|-------------|
| **A — Master data first** (recommended) | Define DB + import for courses, rooms, labs, semesters; then build UI pages for each |
| **B — Faculty UI first** | Fast demo of imported AIML faculty only; other data still needed before allocation |

**Recommendation:** Do **Phase 2a (department master data)** next, then UI pages for faculty + courses + rooms/labs together. Faculty-only UI can be done in parallel if you want something visible quickly.

---

## Current Status

| Area | Status | Notes |
|------|--------|-------|
| Architecture & folder structure | ✅ Done | Clean Architecture layout in place |
| PostgreSQL database | ✅ Done | Docker on port **15432** (avoids local Postgres conflict) |
| Faculty data (AIML) | ✅ Done | 39 faculty, 160 specializations imported |
| Faculty import (Excel) | ✅ Done | CLI script + API endpoint |
| **Subjects / courses (per semester)** | ✅ Done | 81 courses across 3 batches (2022-26, 2023-27, 2024-28); course types incl. PEC/SEC |
| **Classrooms (available)** | ✅ Done | 424, 431, 432, 433, 439 (section-wise theory) |
| **Lecture halls (college)** | ✅ Done | LH-1 … LH-6; PEC/SEC combined 2–3 sections |
| **Laboratories (available)** | ✅ Done | 508, 509, 510 |
| **Semesters / academic year rules** | ✅ Done | Year levels, sections, working days configured |
| Timetable / time slots | ✅ Done | 7 teaching periods + break + lunch (08:30–16:20) |
| Policies (AICTE rules) | ✅ Done | Designation hours, min courses, lab limits, similarity matching, dual-faculty labs |
| Frontend | ✅ Admin UI | Dashboard, faculty, courses, rooms, timetable, policies |
| Optimization engine | ✅ Slice 1–2 | Workload + weekly timetable grid (day/slot/room) |
| AI explanation layer | ❌ Not started | Explain-only; no optimization via LLM |
| Auth / RBAC | ❌ Not started | JWT, dept head, admin roles |
| Reports & analytics | ❌ Not started | PDF/Excel, fairness dashboard |

**Phase:** Phase 5 Slice 2 done → **AI explanations / hard AICTE mins** next

---
## Completed Tasks

### Foundation
- [x] Enterprise folder structure (`backend/`, `frontend/`, `database/`, `infra/`, `docs/`, `tests/`)
- [x] Architecture documentation and ADRs
- [x] `docker-compose.yml` — PostgreSQL + Redis
- [x] `.env.example` and environment variable conventions (`FWP_*`)
- [x] Backend `pyproject.toml` and dependency setup (Python 3.10+)
- [x] Frontend scaffold — React, TypeScript, Tailwind, Vite

### Database & Faculty
- [x] SQLAlchemy models: `departments`, `faculty_members`, `faculty_specializations`
- [x] Database session and settings (`backend/config/settings.py`)
- [x] Excel import service — parses AIML faculty sheet format
- [x] CLI import: `scripts/db/import_faculty.py`
- [x] API: `POST /api/v1/faculty/import`
- [x] API: `GET /api/v1/faculty`
- [x] Import AIML faculty from `AIML_Faculties_Details.xlsx` (39 rows)
- [x] Faculty import guide: `docs/deployment/faculty-import.md`

### Department master data (AIML)
- [x] Models: `academic_year_levels`, `semesters`, `classrooms`, `laboratories`, `courses`
- [x] AIML year rules: 2nd yr (sem 3–4, 5 sections, Mon–Fri), 3rd yr (sem 5–6, 4 sections, Mon–Fri), 4th yr (sem 7, 2 sections, Thu–Fri)
- [x] Seed classrooms: 424, 431, 432, 433, 439
- [x] Seed laboratories: 508, 509, 510
- [x] Course Excel import — batch, course type, 81 rows (`Courses.xlsx`)
- [x] `student_batches` model (2022-26, 2023-27, 2024-28)
- [x] `lecture_halls` model (6 halls, 2–3 combined sections)
- [x] Course fields: `batch_id`, `course_type`, `requires_lecture_hall` (PEC/SEC)
- [x] API: `GET /student-batches`, `/lecture-halls`, courses `?batch=`
- [x] CLI: `scripts/db/seed_aiml_master_data.py`, `scripts/db/import_courses.py`
- [x] API: `POST /api/v1/department/seed-aiml`, `POST /api/v1/courses/import`
- [x] API: `GET /api/v1/courses`, `/classrooms`, `/laboratories`, `/semesters`, `/academic-year-levels`
- [x] Guide: `docs/deployment/aiml-master-data-import.md`

### Timetable (daily periods)
- [x] `time_slots` model (teaching / break / lunch)
- [x] AIML daily schedule: 7 teaching hours 08:30–16:20
- [x] Seed via `seed_aiml_master_data.py` and `POST /api/v1/timetable/seed-aiml`
- [x] API: `GET /api/v1/timetable/slots`, `/timetable/overview`
- [x] Guide: `docs/deployment/aiml-timetable-slots.md`
- [ ] Assign course sessions to specific day + slot + room (grid allocation)

### Workload policies (AICTE)
- [x] `designation_workload_policies` model (theory/lab mins, hours, lab session limits)
- [x] `planning_policies` model (similarity matching, fallback, lab continuity, dual-faculty labs, theory spread, semester-fixed timetable)
- [x] AIML AICTE rules seeded (Assistant / Associate / Professor / Chairperson)
- [x] Fallback rule: no specialization match → Assistant Professor eligible
- [x] **Similarity-based course–faculty matching** (`specialization_matcher.py`, preview API)
- [x] **Lab rule: 2 faculty per laboratory session** (`lab_faculty_per_session`)
- [x] **Semester-fixed weekly timetable** policy (`timetable_fixed_for_semester`)
- [x] API: `GET /api/v1/policies`, `POST /api/v1/policies/seed-aiml`
- [x] API: `GET /api/v1/courses/specialization-matches`
- [x] Guide: `docs/deployment/aiml-workload-policies.md`
- [x] 4th hour timetable confirmed 11:40–12:35

---

## Pending Tasks

### Phase 2a — Department master data (do before optimization)

> **Most Phase 2a items complete.** Remaining: room capacity, Alembic migrations.

#### Semesters & structure
- [x] `semesters` + `academic_year_levels` models
- [x] Link courses to semester and year level
- [ ] Academic term / active semester flag (e.g. `2025-26 Odd`)

#### Subjects / courses (per semester)
- [x] Course ORM models (code, name, credits, semester, lectures_per_week, practical_hours)
- [x] Practical hours = continuous lab block duration
- [x] Required specialization per course — **inferred at planning time** via similarity matching (no manual table)
- [x] Course Excel import (`Courses.xlsx` format)
- [x] API: list / import courses by semester
- [x] AIML subject list imported (26 courses, sem 3–7)

#### Classrooms (available to department)
- [x] `classrooms` model and AIML inventory seeded
- [x] API: list classrooms
- [x] Teaching classrooms distinct from faculty cabin numbers

#### Laboratories (available to department)
- [x] `laboratories` model and AIML inventory seeded
- [x] API: list laboratories
- [ ] Lab capacity / equipment notes (optional)
- [ ] Link lab courses to specific lab rooms (optimizer phase)

#### Data collection (from department)
- [x] AIML semester-wise subject list (`Courses.xlsx`)
- [x] Classroom list allocated to AIML
- [x] Laboratory list allocated to AIML

### Phase 2b — Admin UI (after or parallel with 2a APIs)

- [x] Basic app layout (sidebar, header, routing)
- [x] Dashboard with summary stats
- [x] Faculty list page (`GET /api/v1/faculty`)
- [x] Subjects / courses list page (filter by semester)
- [x] Classrooms list page
- [x] Laboratories list page
- [x] Timetable daily periods page
- [x] Policies page (AICTE designation rules)
- [x] API client modules in `frontend/src/api/`
- [x] Loading and error states on list pages

### Phase 2c — Database hygiene
- [ ] Alembic migrations (replace `create_all` bootstrap)
- [ ] Migrations for faculty + courses + rooms + labs tables
- [ ] Seed reference data scripts documented

### Phase 3 — Timetable & time slots
- [x] Daily time period template (7 teaching + break + lunch)
- [x] Policy: weekly grid fixed for entire semester once set
- [ ] Weekly grid: assign theory sessions to classroom + day + slot
- [ ] Weekly grid: assign lab sessions to laboratory + continuous slots (2 faculty per session)
- [ ] Conflict detection (room double-booking, faculty clash)
- [ ] API: timetable assignment CRUD or import

### Phase 4 — Policies
- [x] Policy models (designation workload + planning rules)
- [x] AICTE seed data for AIML designations
- [x] API to read / seed policies
- [x] Course–faculty similarity matching (runtime inference, not mapping table)

**Phase:** Phase 5 Slice 1 done → **Timetable grid (Slice 2)** next

### Phase 5 — Optimization engine (Slice 1 ✅)
- [x] `optimization/models/problem_definition.py` — input contracts
- [x] `optimization/preprocessing/slot_builder.py` — theory/lab slots, PEC/SEC LH groups
- [x] `optimization/preprocessing/eligibility.py` — specialization similarity + AP fallback
- [x] `optimization/engine/cpsat_solver.py` — OR-Tools CP-SAT
- [x] `optimization/postprocessing/validator.py` — AICTE policy warnings
- [x] `allocation_runs` model + `AllocationService`
- [x] API: `POST /api/v1/allocations/run`, `GET /api/v1/allocations/{id}`
- [x] Admin UI: Allocation page
- [x] Unit tests: slot builder + tiny CP-SAT scenario

### Phase 5 — Optimization engine (Slice 2 ✅)
- [x] Weekly timetable CP-SAT (`timetable_cpsat_solver.py`)
- [x] Theory sessions spread across working days; labs in continuous blocks (no lunch crossing)
- [x] Room assignment: classrooms, lecture halls (PEC/SEC), laboratories
- [x] Conflicts: faculty, room, student section per day+period
- [x] Semester-fixed weekly grid stored in `allocation_runs.solution`
- [x] UI: weekly timetable view on Allocation page

### Phase 5 — Optimization engine (Slice 3 — pending)
- [ ] Hard AICTE minimum hours/courses per faculty (currently warnings only)
- [ ] Faculty preference / leave constraints
- [ ] Explainability payload for LLM layer
- [ ] Objectives: fairness, preference satisfaction, workload balance
- [ ] CP-SAT solver integration (`optimization/engine/cpsat_solver.py`)
- [ ] Postprocessing: solution validator, conflict report, explainability payload
- [ ] API: `POST /api/v1/allocations/run`
- [ ] API: get allocation run status and results
- [ ] Unit tests for constraints (positive + negative cases)
- [ ] Small benchmark scenario (5 faculty, 5 courses) before full department

### Phase 6 — AI explanation layer
- [ ] LLM client factory (NIM / OpenAI / Groq)
- [ ] Explanation chain — reads optimization output only
- [ ] Prompt templates and guardrails (no invented assignments)
- [ ] API: explain allocation / summarize conflicts
- [ ] Frontend: explanation panel for admin review

### Phase 7 — Auth, workflow, reports
- [ ] User model and JWT authentication
- [ ] RBAC (admin, dept head, faculty, viewer)
- [ ] Approval workflow for allocation plans
- [ ] Faculty workload reports (PDF / Excel export)
- [ ] Department summary and conflict reports
- [ ] Analytics dashboard (fairness score, utilization)
- [ ] Email / in-app notifications

### Phase 8 — Production & demo readiness
- [ ] Backend Dockerfile fully wired
- [ ] Full stack in Docker Compose (api + frontend + worker)
- [ ] CI pipeline green (lint + unit tests)
- [ ] Prometheus / Grafana dashboards (optional for demo)
- [ ] Deployment guide (Railway / Render / university hosting)
- [ ] Capstone demo script and sample walkthrough

---

## Priority Matrix (capstone demo)

| Priority | Task | Why |
|----------|------|-----|
| 🔴 High | Subjects/courses per semester (schema + data) | Defines **what** must be allocated |
| 🔴 High | Classrooms + laboratories (schema + data) | Defines **where** theory/labs run |
| 🔴 High | Basic CP-SAT allocation run | Proves decision-support, not chatbot |
| 🟡 Medium | Faculty + master data list UIs | Makes system usable for dept admin |
| 🟡 Medium | Timetable / time slots | Needed for full conflict-free planning |
| 🟡 Medium | AICTE policy constraints | Real-world stakeholder rules |
| 🟡 Medium | AI explanations | NVIDIA / LLM story |
| 🟢 Lower | Auth, notifications, full reports | Production polish |

---

## Suggested order (revised)

1. ~~Semesters + subjects/courses~~ ✅  
2. ~~Classrooms + laboratories~~ ✅  
3. **Admin UI** — faculty, courses, rooms, labs list pages  
4. **Alembic migrations** — all master data tables  
5. **Timetable / time slots** — spread lectures across working days; continuous lab blocks  
6. **Policies** — AICTE teaching hour limits  
7. **Minimal optimizer** — faculty specialization → courses + hour limits + sections  

---

## Data inventory

| Dataset | Format | Status | Notes |
|---------|--------|--------|-------|
| AIML faculty | Excel | ✅ Imported | 39 faculty, dept `AI&ML`, specializations |
| Faculty cabins | Excel (col on faculty sheet) | ✅ Imported | `cabin_number` on faculty row |
| **Subjects / courses** | Excel | ✅ Ready | 81 rows, 3 batches; re-import with `--replace` |
| **Lecture halls** | Config | ✅ Seeded | LH-1 … LH-6; PEC/SEC combined sections |
| **Classrooms** | Config | ✅ Seeded | 424, 431, 432, 433, 439 |
| **Laboratories** | Config | ✅ Seeded | 508, 509, 510 |
| **Semesters / year rules** | Config | ✅ Seeded | Sections + working days per year level |
| Timetable daily periods | Config | ✅ Seeded | 7 teaching slots; break 10:20–10:45; lunch 12:35–13:50 |
| Timetable weekly grid | — | ❌ Needed | Day + slot + room assignments per section |
| AICTE / dept policies | Config | ✅ Seeded | Designation rules + similarity matching + dual-faculty labs + semester-fixed grid |
| Faculty preferences | Form / Excel | ❌ Later | Subject preferences, leave |
---

## Key commands

```powershell
# Start database
docker compose up -d postgres

# Import faculty Excel
python scripts/db/import_faculty.py "C:\path\to\AIML_Faculties_Details.xlsx"

# Seed AIML rooms + semesters, then import courses
python scripts/db/import_courses.py "C:\path\to\Courses.xlsx"

# Start backend
uvicorn backend.main:app --reload

# Run workload allocation (example)
curl -X POST http://127.0.0.1:8000/api/v1/allocations/run -H "Content-Type: application/json" -d "{\"batch_code\":\"2023-27\",\"semester_number\":5}"

# Start frontend
cd frontend && npm run dev
```

- API docs: http://localhost:8000/docs  
- Frontend: http://localhost:5173  
- DB URL: `127.0.0.1:15432` (see `.env`)

---

## How to update this file

1. When a task is done, move `- [ ]` → `- [x]` under the right section.
2. Optionally move completed items from **Pending** to **Completed Tasks**.
3. Update **Current Status** table and **Last updated** date at the top.
4. Add new tasks under the relevant phase as scope grows.

---

## References

- [Architecture overview](architecture/overview.md)
- [Optimization design](architecture/optimization-design.md)
- [AI layer design](architecture/ai-layer-design.md)
- [Faculty import guide](deployment/faculty-import.md)
- [AIML master data & course import](deployment/aiml-master-data-import.md)
- [AIML timetable slots](deployment/aiml-timetable-slots.md)
- [AIML workload policies](deployment/aiml-workload-policies.md)
- Stakeholder requirements: `InitialSurvey-Ans.docx` (project root)
