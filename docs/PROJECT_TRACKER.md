# Faculty Workload Planning Agent — Project Tracker

> Living document for tracking completed and pending work.  
> **Last updated:** 2026-07-12 (batch department reports, optional AI narrative)

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
Optimization run                                  ✅ done (multi-batch)
```

| Approach | When to use |
|----------|-------------|
| **A — Master data first** (recommended) | Define DB + import for courses, rooms, labs, semesters; then build UI pages for each |
| **B — Faculty UI first** | Fast demo of imported AIML faculty only; other data still needed before allocation |

**Recommendation:** Focus next on **AI explanation layer**, **batch-wise export**, and **hard AICTE minimums** — core allocation + timetable path is working.

---

## Current Status

| Area | Status | Notes |
|------|--------|-------|
| Architecture & folder structure | ✅ Done | Clean Architecture layout in place |
| PostgreSQL database | ✅ Done | Docker on port **15432** (avoids local Postgres conflict) |
| Faculty data (AIML) | ✅ Done | 39 faculty, 160 specializations imported |
| Faculty import (Excel) | ✅ Done | CLI script + API endpoint |
| **Subjects / courses (per semester)** | ✅ Done | **133 courses** across 3 batches; types IPCC, PCC, SEC, BSC, HSMC, **PEC 1–5** |
| **Classrooms (available)** | ✅ Done | 424, 431, 432, 433, 439 (section-wise theory) |
| **Lecture halls (college)** | ✅ Done | LH-1 … LH-6; PEC/SEC combined 2–3 sections |
| **Laboratories (available)** | ✅ Done | 508, 509, 510 |
| **Semesters / academic year rules** | ✅ Done | Year levels, sections, working days configured |
| Timetable / time slots | ✅ Done | 7 teaching periods + break + lunch (08:30–16:20) |
| Policies (AICTE rules) | ✅ Done | Designation hours, min courses, lab limits, similarity matching, dual-faculty labs |
| Frontend | ✅ Admin UI | Dashboard, faculty, courses, rooms, timetable, policies, **allocations + timetable grids** |
| Optimization engine | ✅ Slice 1–2+ | Workload CP-SAT/greedy + weekly timetable (greedy default; CP-SAT available) |
| **Lab scheduling (B1/B2)** | ✅ Done | Mandatory B1 + B2 sub-batches; 2 h/week each; capacity 35; 2 faculty per lab |
| **PEC enrollment & room rules** | ✅ Done | Per-course student counts; >150 → LH, ≤150 → classroom; SEC always LH; parallel pool timing **disabled** |
| **Roomless courses** | ✅ Done | UG Research Project — no classroom/lab reserved |
| **Allocation UX** | ✅ Done | Multi-batch runs, save/load plans, editable assignments, section/faculty/room/lab grid views |
| AI explanation layer | 🟡 Partial | Batch report generator + optional NIM narrative; interactive agent not started |
| Auth / RBAC | ❌ Not started | JWT, dept head, admin roles |
| Reports & analytics | 🟡 Partial | Batch markdown report; full PDF/Excel export pending |

**Phase:** Phase 6 started (batch reports) → **interactive AI advisor / batch Excel export** next

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
- [x] Course Excel import — batch, course type, **`data/master/Courses.xlsx` (133 rows)**
- [x] `student_batches` model (2022-26, 2023-27, 2024-28)
- [x] `lecture_halls` model (6 halls, 2–3 combined sections)
- [x] Course fields: `batch_id`, `course_type`, `requires_lecture_hall` (PEC/SEC)
- [x] **PEC elective groups:** PEC 1 … PEC 5 validated in `course_type_config.py`
- [x] API: `GET /student-batches`, `/lecture-halls`, courses `?batch=`
- [x] CLI: `scripts/db/seed_aiml_master_data.py`, `scripts/db/import_courses.py --replace`
- [x] API: `POST /api/v1/department/seed-aiml`, `POST /api/v1/courses/import`
- [x] API: `GET /api/v1/courses`, `/classrooms`, `/laboratories`, `/semesters`, `/academic-year-levels`
- [x] Guide: `docs/deployment/aiml-master-data-import.md`

### Timetable (daily periods)
- [x] `time_slots` model (teaching / break / lunch)
- [x] AIML daily schedule: 7 teaching hours 08:30–16:20
- [x] Seed via `seed_aiml_master_data.py` and `POST /api/v1/timetable/seed-aiml`
- [x] API: `GET /api/v1/timetable/slots`, `/timetable/overview`
- [x] Guide: `docs/deployment/aiml-timetable-slots.md`
- [x] Assign course sessions to specific day + slot + room (weekly grid via allocation run)

### Workload policies (AICTE)
- [x] `designation_workload_policies` model (theory/lab mins, hours, lab session limits)
- [x] `planning_policies` model (similarity matching, fallback, lab continuity, dual-faculty labs, theory spread, semester-fixed timetable)
- [x] AIML AICTE rules seeded (Assistant / Associate / Professor / Chairperson)
- [x] Fallback rule: no specialization match → Assistant Professor eligible
- [x] **Similarity-based course–faculty matching** (`specialization_matcher.py`, preview API)
- [x] **Lab rule: 2 faculty per laboratory session** (`lab_faculty_per_session`)
- [x] **Semester-fixed weekly timetable** policy (`timetable_fixed_for_semester`)
- [x] **Lab B1/B2 sub-batches** — both mandatory; 2-hour blocks; max 35 students per sub-batch (`lab_config.py`)
- [x] **SEC theory-only** — no laboratory practicals (`course_type_config.py`)
- [x] **PEC room rules** — >150 students → lecture hall; ≤150 → classrooms; SEC always LH (`pec_config.py`)
- [x] **PEC parallel pool timing** — policy present, **currently disabled** (electives may schedule at different times)
- [x] **Roomless delivery** — UG Research Project scheduled without room allocation
- [x] API: `GET /api/v1/policies`, `POST /api/v1/policies/seed-aiml`
- [x] API: `GET /api/v1/courses/specialization-matches`
- [x] Guide: `docs/deployment/aiml-workload-policies.md`
- [x] 4th hour timetable confirmed 11:40–12:35

### Phase 2b — Admin UI
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

### Phase 5 — Optimization engine (Slice 1 ✅)
- [x] `optimization/models/problem_definition.py` — input contracts
- [x] `optimization/preprocessing/slot_builder.py` — theory/lab slots, PEC/SEC LH groups, B1/B2 lab slots
- [x] `optimization/preprocessing/eligibility.py` — specialization similarity + AP fallback
- [x] `optimization/engine/cpsat_solver.py` — OR-Tools CP-SAT (workload)
- [x] `optimization/engine/greedy_workload_allocator.py` — greedy workload fallback
- [x] `optimization/postprocessing/validator.py` — AICTE policy warnings
- [x] `allocation_runs` model + `AllocationService`
- [x] API: `POST /api/v1/allocations/run`, `GET /api/v1/allocations/{id}`, `PATCH` save/edit
- [x] **Multi-batch allocation** — one run across selected batches with per-batch semester
- [x] **PEC per-course enrollment** — only courses with student count > 0 included in plan
- [x] Admin UI: Allocation page with batch/semester selection
- [x] Unit tests: slot builder, CP-SAT, greedy allocator, PEC rules, lab sub-batches (**46 tests**)

### Phase 5 — Optimization engine (Slice 2 ✅)
- [x] Weekly timetable CP-SAT (`timetable_cpsat_solver.py`)
- [x] **Greedy timetable scheduler** (`greedy_timetable_scheduler.py`) — default for multi-batch runs
- [x] Theory sessions spread across working days; labs in continuous blocks (no lunch crossing)
- [x] Room assignment: classrooms, lecture halls (PEC/SEC), laboratories; **roomless** for UG Research Project
- [x] Conflicts: faculty, room, student section per day+period; B1/B2 parallel lab subjects allowed
- [x] Semester-fixed weekly grid stored in `allocation_runs.solution`
- [x] `timetable_grid_service.py` — section, faculty, classroom, laboratory grid builders

### Phase 5 — Allocation & timetable UI (Slice 2b ✅)
- [x] **Timetable grid views** — by batch/section, combined department, faculty, classroom, laboratory
- [x] **Session colour coding** — theory, PEC, SEC, lab
- [x] **PEC enrollment UI** — per-course student counts grouped by PEC pool (PEC 1–5)
- [x] **Faculty contacts table** — under section grid; merged cells for multi-teacher labs; course type column
- [x] **Lab faculty names** — shown in laboratory timetable view only
- [x] **Editable assignments table** — manual faculty reassignment before save
- [x] **Save / load allocation plans** — named runs, previous-run picker
- [x] Allocation progress panel for long runs

### Phase 6 — Batch department reports (Slice 1 ✅)
- [x] `allocation_report_service.py` — grounded facts + markdown for HOD review
- [x] API: `POST /api/v1/allocations/{run_id}/reports/batch-summary`
- [x] Optional LLM executive summary via `backend/ai/llm/client.py`
- [x] Frontend `AllocationReportPanel` — generate, preview, download `.md`, print/PDF
- [x] Unit tests: `test_allocation_report_service.py`

---

## Pending Tasks

### Phase 2c — Database hygiene
- [ ] Alembic migrations (replace `create_all` bootstrap)
- [ ] Migrations for faculty + courses + rooms + labs tables
- [ ] Seed reference data scripts documented

### Phase 3 — Timetable (remaining)
- [ ] Academic term / active semester flag (e.g. `2025-26 Odd`)
- [ ] Lab capacity / equipment notes (optional metadata)
- [ ] Link lab courses to specific lab rooms (optimizer preference, not hard constraint)
- [ ] Standalone timetable assignment CRUD or import (outside allocation run)

### Phase 5 — Optimization engine (Slice 3 — pending)
- [ ] Hard AICTE minimum hours/courses per faculty (currently warnings only)
- [ ] Faculty preference / leave constraints
- [ ] Explainability payload for LLM layer (structured JSON from validator + assignments)
- [ ] Objectives: fairness, preference satisfaction, workload balance (soft CP-SAT objectives)
- [ ] Re-enable PEC parallel pool timing as optional policy flag
- [ ] Larger benchmark / performance tests for full department

### Phase 6 — AI explanation layer
- [x] **Batch summary report** — deterministic markdown (`POST /allocations/{id}/reports/batch-summary`)
- [x] Report facts aggregator (workload, PEC, labs, rooms, violations)
- [x] Minimal LLM client (`backend/ai/llm/client.py`) — NIM / OpenAI / Groq
- [x] Optional AI executive summary when `FWP_AI_ENABLED=true`
- [x] Frontend report panel (generate, download Markdown, print/PDF)
- [ ] Full agent with tools (interactive Q&A over allocation runs)
- [ ] Prompt guardrails wired into all AI flows
- [ ] API: explain allocation / summarize conflicts (chat)
- [ ] Frontend: explanation chat panel for admin review
- [ ] **Suggested model:** NVIDIA NIM `meta/llama-3.1-70b-instruct` (primary); OpenAI `gpt-4o-mini` (dev fallback)

### Phase 7 — Auth, workflow, reports
- [ ] User model and JWT authentication
- [ ] RBAC (admin, dept head, faculty, viewer)
- [ ] Approval workflow for allocation plans
- [ ] **Batch-wise export** — CSV/Excel per batch (section timetable + faculty contacts + assignments)
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
| ✅ Done | Subjects/courses per semester | Defines **what** must be allocated |
| ✅ Done | Classrooms + laboratories | Defines **where** theory/labs run |
| ✅ Done | CP-SAT / greedy allocation + timetable | Proves decision-support, not chatbot |
| ✅ Done | Admin UI + allocation/timetable views | Usable for dept admin demo |
| 🟡 Medium | **AI explanations (NIM)** | NVIDIA / LLM story; explain-only |
| 🟡 Medium | **Batch-wise Excel/CSV export** | Stakeholder deliverable |
| 🟡 Medium | Hard AICTE minimum constraints | Real-world policy enforcement |
| 🟢 Lower | Auth, notifications, full analytics | Production polish |

---

## Suggested order (revised)

1. ~~Semesters + subjects/courses~~ ✅  
2. ~~Classrooms + laboratories~~ ✅  
3. ~~Admin UI — faculty, courses, rooms, labs~~ ✅  
4. ~~Timetable / time slots + weekly grid allocation~~ ✅  
5. ~~Policies — AICTE, labs, PEC/SEC rules~~ ✅  
6. ~~Minimal optimizer + multi-batch timetable UI~~ ✅  
7. **Alembic migrations** — production DB hygiene  
8. **Batch-wise export** — CSV/Excel per batch  
9. **AI explanation layer** — NIM explain-only panel  
10. **Hard AICTE mins + auth** — production readiness  

---

## Data inventory

| Dataset | Format | Status | Notes |
|---------|--------|--------|-------|
| AIML faculty | Excel | ✅ Imported | 39 faculty, dept `AI&ML`, specializations |
| Faculty cabins | Excel (col on faculty sheet) | ✅ Imported | `cabin_number` on faculty row |
| **Subjects / courses** | Excel | ✅ Ready | **133 rows**, 3 batches; PEC 1–5; `data/master/Courses.xlsx` |
| **Lecture halls** | Config | ✅ Seeded | LH-1 … LH-6; PEC/SEC combined sections |
| **Classrooms** | Config | ✅ Seeded | 424, 431, 432, 433, 439 |
| **Laboratories** | Config | ✅ Seeded | 508, 509, 510 |
| **Semesters / year rules** | Config | ✅ Seeded | Sections + working days per year level |
| Timetable daily periods | Config | ✅ Seeded | 7 teaching slots; break 10:20–10:45; lunch 12:35–13:50 |
| Timetable weekly grid | Allocation run | ✅ Generated | Stored in `allocation_runs.solution` |
| PEC enrollment counts | UI / API | ✅ Supported | Per-course counts per batch in allocation request |
| AICTE / dept policies | Config | ✅ Seeded | Labs, PEC room rules, similarity matching, roomless courses |
| Faculty preferences | Form / Excel | ❌ Later | Subject preferences, leave |
| AI / LLM | Config only | ❌ Not wired | NIM, OpenAI, Groq in `configs/ai_providers.yaml` |

---

## Key commands

```powershell
# Start database
docker compose up -d postgres

# Import faculty Excel
python scripts/db/import_faculty.py "C:\path\to\AIML_Faculties_Details.xlsx"

# Import course catalog (133 courses, 3 batches)
python scripts/db/import_courses.py "data/master/Courses.xlsx" --replace

# Seed AIML rooms + semesters (if fresh DB)
python scripts/db/seed_aiml_master_data.py

# Start backend
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Run unit tests
python -m pytest tests/unit/ -q

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
