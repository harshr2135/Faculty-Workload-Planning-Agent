# Faculty Workload Planning Agent — Project Tracker

> Living document for tracking completed and pending work.  
> **Last updated:** 2026-07-25 (teaching-load half-weight for labs, designation hour caps 4/8/12/16, timetable Excel+PDF export packs, faculty timetable email)

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


| Approach                                | When to use                                                                          |
| --------------------------------------- | ------------------------------------------------------------------------------------ |
| **A — Master data first** (recommended) | Define DB + import for courses, rooms, labs, semesters; then build UI pages for each |
| **B — Faculty UI first**                | Fast demo of imported AIML faculty only; other data still needed before allocation   |


**Recommendation:** Core allocation + timetable + CP-SAT + reports + **timetable export/email** are working. Focus next on **faculty subject preferences** (soft objective), **hard AICTE minimums**, and **interactive AI advisor**.

---



## Current Status


| Area                                  | Status        | Notes                                                                                                                                             |
| ------------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| Architecture & folder structure       | ✅ Done        | Clean Architecture layout in place                                                                                                                |
| PostgreSQL database                   | ✅ Done        | Docker on port **15432** (avoids local Postgres conflict)                                                                                         |
| Faculty data (AIML)                   | ✅ Done        | 39 faculty, 160 specializations imported                                                                                                          |
| Faculty import (Excel)                | ✅ Done        | CLI script + API endpoint                                                                                                                         |
| **Subjects / courses (per semester)** | ✅ Done        | **133 courses** across 3 batches; types IPCC, PCC, SEC, BSC, HSMC, **PEC 1–5**                                                                    |
| **Classrooms (available)**            | ✅ Done        | 424, 431, 432, 433, 439 (section-wise theory)                                                                                                     |
| **Lecture halls (college)**           | ✅ Done        | LH-1 … LH-6; PEC/SEC combined 2–3 sections                                                                                                        |
| **Laboratories (available)**          | ✅ Done        | 508, 509, 510                                                                                                                                     |
| **Semesters / academic year rules**   | ✅ Done        | Year levels, sections, working days configured                                                                                                    |
| Timetable / time slots                | ✅ Done        | 7 teaching periods + break + lunch (08:30–16:20)                                                                                                  |
| Policies (AICTE rules)                | ✅ Done        | Designation **max teaching-load hours** (Chair 4 / Prof 8 / Assoc 12 / Asst 16); **2 lab/tutorial contact hours = 1 teaching hour**; lab-session max uncapped for now; similarity matching; dual-faculty labs |
| Frontend                              | ✅ Admin UI    | Dashboard, faculty, courses, rooms, timetable, policies, **allocations + grids + Excel/PDF export + faculty email**                                                                                          |
| Optimization engine                   | ✅ Slice 1–3   | **Workload CP-SAT default** + weekly timetable; hard teaching-load caps (lab half-weight); cap-proportional balancing; greedy retained as fallback                                                          |
| **Lab scheduling (B1/B2)**            | ✅ Done        | Mandatory B1 + B2 sub-batches; 2 h/week each; capacity 35; 2 faculty per lab                                                                                                                                  |
| **PEC enrollment & room rules**       | ✅ Done        | Per-course student counts; >150 → LH, ≤150 → classroom; SEC always LH; parallel pool timing **disabled**                                                                                                      |
| **Roomless courses**                  | ✅ Done        | UG Research Project — no classroom/lab reserved                                                                                                                                                               |
| **Allocation UX**                     | ✅ Done        | Multi-batch runs, save/load plans, section/faculty/room/lab grids, **Excel+PDF export**, **email faculty PDFs**                                                                                               |
| AI explanation layer                  | 🟡 Partial    | Batch + all-batches LLM full-facts reports (streaming); interactive agent not started                                                                                                                         |
| Auth / RBAC                           | ❌ Not started | JWT, dept head, admin roles                                                                                                                                                                                   |
| Reports & analytics                   | 🟡 Partial    | LLM/markdown reports + overall faculty allocation; **timetable Excel/PDF packs done**; deeper analytics / approval workflow pending                                                                           |


**Phase:** Timetable stakeholder deliverables (export + email) done → **faculty preferences (soft objective) / hard AICTE minimums / interactive AI advisor** next

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
- [x] Course Excel import — batch, course type, `data/master/Courses.xlsx` **(133 rows)**
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
- [x] **Weekly max teaching-load hours** — Chairperson 4, Professor 8, Associate 12, Assistant 16 (`policy_config.py`; re-seed via `POST /policies/seed-aiml`)
- [x] **Lab/tutorial teaching-load weight** — 2 contact hours = 1 teaching hour (`lab_tutorial_hours_per_teaching_hour`); theory 1:1; timetable still uses full contact duration
- [x] **Lab-session designation max** — currently uncapped (`min_lab_sessions` / `max_lab_sessions` null); soft overage logic retained for later
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



### Phase 5/6 — CP-SAT default engine + policy & reporting refinements (✅)

- [x] **CP-SAT is now the active workload engine** (`allocation_service` → `WorkloadCpsatSolver`); greedy kept as fallback
- [x] **Hard AICTE weekly-hour caps** — teaching load may never exceed designation max (lab/tutorial at half weight; infeasible if capacity is short)
- [x] Soft lab-session maximums — code retained; **currently uncapped** in seeded policies
- [x] **Cap-proportional (utilization) load balancing** — hours distributed in proportion to designation caps via L1 utilization spread; sentinel/zero-cap guards; peak-load fallback when <2 real caps
- [x] **Lexicographic objective** — specialization/policy quality strictly dominates balancing (never trades teaching fit for evenness)
- [x] CP-SAT `_extract_assignments` now preserves `lab_sub_batch` (B1/B2) and `requires_lecture_hall`
- [x] **All-batches combined report** — `POST /api/v1/allocations/{run_id}/reports/all-batches`; per-batch sections generated concurrently
- [x] **Consolidated faculty workload table** — run-wide load distribution across all batches
- [x] **LLM full-facts report mode** — model renders full report from pre-aggregated facts JSON; HTML/Markdown views + print
- [x] **Designation label** — shared `designation_label_for()` (single source); shown in reports **and** the after-allocation faculty workload table (auto-derived via schema validator)
- [x] Unit tests updated for hard caps, cap-proportional split, specialization dominance (**68 tests**)



### Phase 6b — Report scope & teaching load (✅)

- [x] Overall faculty allocation once per report (not repeated per-batch hour tables)
- [x] Faculty teaching-by-batch subject lists in reports
- [x] Policy warnings scoped with overall allocation (not duplicated per batch)
- [x] Report streaming SSE (`…/reports/batch-summary/stream`, `…/all-batches/stream`)
- [x] Teaching-load totals in reports/UI vs AICTE max (theory contact + lab/2)



### Phase 7a — Timetable export & faculty email (✅)

- [x] **Three Excel packs** — faculty (sheet/page per person), students (per class/section), rooms & labs (per room)
- [x] **Three PDF packs** — same scopes; landscape A4 one page per entity (`reportlab`)
- [x] API: `GET /allocations/{run_id}/export/timetable/{faculty|students|rooms}?format=xlsx|pdf`
- [x] Allocations UI download buttons (Excel + PDF rows)
- [x] **Email faculty timetables** — one personal PDF per faculty with load; SMTP via `FWP_SMTP_*`
- [x] API: `POST /allocations/{run_id}/email/faculty-timetables` (sent / skipped / failed summary)
- [x] Unit tests: export packs + mail service (mocked SMTP)

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



### Phase 5 — Optimization engine (Slice 3)

- [x] **Hard AICTE weekly-hour maximums** per faculty (blocking; teaching-load units with lab half-weight)
- [x] **Workload balance objective** — cap-proportional utilization balancing (soft CP-SAT objective)
- [x] **Lab/tutorial → teaching-hour conversion** (`teaching_load.py`; policy `lab_tutorial_hours_per_teaching_hour=2`)
- [ ] Hard AICTE **minimum** hours/courses per faculty (currently warnings only)
- [ ] Re-enable or configure soft **lab-session max** per designation (currently uncapped)
- [ ] **Faculty subject preferences** — capture ranked preference data, then add a soft `preference_penalty` objective + preference-satisfaction fairness spread (refines choice among eligible specialists; leave constraints)
- [ ] **Tiered eligibility** (optional) — specialists → same-designation → fallback, so the balancer has room to honor cap ratios when specialists are scarce
- [ ] Explainability payload for LLM layer (structured JSON from validator + assignments)
- [ ] Re-enable PEC parallel pool timing as optional policy flag
- [ ] Larger benchmark / performance tests for full department



### Phase 6 — AI explanation layer

- [x] **Batch summary report** — deterministic markdown (`POST /allocations/{id}/reports/batch-summary`)
- [x] **All-batches combined report** (`POST /allocations/{id}/reports/all-batches`) + consolidated faculty workload table
- [x] Report facts aggregator (workload, PEC, labs, rooms, violations, designation labels)
- [x] Minimal LLM client (`backend/ai/llm/client.py`) — NIM / OpenAI / Groq
- [x] Optional AI executive summary when `FWP_AI_ENABLED=true`
- [x] **LLM full-facts report mode** — model renders the full report from grounded facts JSON
- [x] Frontend report panel (generate, formatted/Markdown views, download Markdown, print/PDF)
- [ ] Full agent with tools (interactive Q&A over allocation runs)
- [ ] Prompt guardrails wired into all AI flows
- [ ] API: explain allocation / summarize conflicts (chat)
- [ ] Frontend: explanation chat panel for admin review
- [ ] **Suggested model:** NVIDIA NIM `meta/llama-3.1-70b-instruct` (primary); OpenAI `gpt-4o-mini` (dev fallback)



### Phase 7 — Auth, workflow, reports

- [ ] User model and JWT authentication
- [ ] RBAC (admin, dept head, faculty, viewer)
- [ ] Approval workflow for allocation plans
- [x] **Timetable export** — Excel + PDF packs (faculty / students / rooms & labs)
- [x] **Faculty timetable email** — personal PDF via SMTP (`FWP_SMTP_*`; not sent until host configured)
- [ ] Student / room email packs (optional)
- [ ] Department summary and conflict reports (beyond current markdown/LLM)
- [ ] Analytics dashboard (fairness score, utilization)
- [ ] Broader in-app notifications



### Phase 8 — Production & demo readiness

- [ ] Backend Dockerfile fully wired
- [ ] Full stack in Docker Compose (api + frontend + worker)
- [ ] CI pipeline green (lint + unit tests)
- [ ] Prometheus / Grafana dashboards (optional for demo)
- [ ] Deployment guide (Railway / Render / university hosting)
- [ ] Capstone demo script and sample walkthrough

---



## Priority Matrix (capstone demo)


| Priority  | Task                                                                | Why                                      |
| --------- | ------------------------------------------------------------------- | ---------------------------------------- |
| ✅ Done    | Subjects/courses per semester                                       | Defines **what** must be allocated       |
| ✅ Done    | Classrooms + laboratories                                           | Defines **where** theory/labs run        |
| ✅ Done    | CP-SAT allocation (hard caps, cap-proportional balance) + timetable | Proves decision-support, not chatbot     |
| ✅ Done    | Admin UI + allocation/timetable views                               | Usable for dept admin demo               |
| ✅ Done    | **LLM reports (per-batch + all-batches)**                           | NVIDIA / LLM story; explain-only         |
| ✅ Done    | **Timetable Excel/PDF export + faculty email**                      | Stakeholder deliverable                  |
| 🟡 Medium | **Faculty subject preferences (soft objective)**                    | Fairer choice among eligible specialists |
| 🟡 Medium | Hard AICTE minimum constraints                                      | Real-world policy enforcement            |
| 🟢 Lower  | Auth, notifications, full analytics                                 | Production polish                        |


---



## Suggested order (revised)

1. ~~Semesters + subjects/courses~~ ✅
2. ~~Classrooms + laboratories~~ ✅
3. ~~Admin UI — faculty, courses, rooms, labs~~ ✅
4. ~~Timetable / time slots + weekly grid allocation~~ ✅
5. ~~Policies — AICTE, labs, PEC/SEC rules~~ ✅
6. ~~Minimal optimizer + multi-batch timetable UI~~ ✅
7. ~~CP-SAT default + hard hour caps + cap-proportional balancing~~ ✅
8. ~~AI explanation layer — per-batch + all-batches LLM reports~~ ✅
9. ~~Timetable Excel/PDF export packs + faculty timetable email~~ ✅
10. **Faculty subject preferences** — soft objective + satisfaction fairness
11. **Alembic migrations** — production DB hygiene
12. **Hard AICTE mins + auth** — production readiness

---



## Data inventory


| Dataset                    | Format                       | Status      | Notes                                                                                                                                                              |
| -------------------------- | ---------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| AIML faculty               | Excel                        | ✅ Imported  | 39 faculty, dept `AI&ML`, specializations                                                                                                                          |
| Faculty cabins             | Excel (col on faculty sheet) | ✅ Imported  | `cabin_number` on faculty row                                                                                                                                      |
| **Subjects / courses**     | Excel                        | ✅ Ready     | **133 rows**, 3 batches; PEC 1–5; `data/master/Courses.xlsx`                                                                                                       |
| **Lecture halls**          | Config                       | ✅ Seeded    | LH-1 … LH-6; PEC/SEC combined sections                                                                                                                             |
| **Classrooms**             | Config                       | ✅ Seeded    | 424, 431, 432, 433, 439                                                                                                                                            |
| **Laboratories**           | Config                       | ✅ Seeded    | 508, 509, 510                                                                                                                                                      |
| **Semesters / year rules** | Config                       | ✅ Seeded    | Sections + working days per year level                                                                                                                             |
| Timetable daily periods    | Config                       | ✅ Seeded    | 7 teaching slots; break 10:20–10:45; lunch 12:35–13:50                                                                                                             |
| Timetable weekly grid      | Allocation run               | ✅ Generated | Stored in `allocation_runs.solution`                                                                                                                               |
| PEC enrollment counts      | UI / API                     | ✅ Supported | Per-course counts per batch in allocation request                                                                                                                  |
| AICTE / dept policies      | Config                       | ✅ Seeded    | Max hours 4/8/12/16; lab/tutorial half-weight; lab-session max uncapped; PEC room rules; similarity matching                                                         |
| Faculty preferences        | Form / Excel                 | ❌ Later     | Ranked subject preferences + leave; planned as soft CP-SAT objective (`preference_penalty`) with satisfaction fairness — refines choice among eligible specialists |
| AI / LLM                   | Config + reports             | 🟡 Partial  | NIM / OpenAI / Groq wired for batch reports when `FWP_AI_ENABLED=true`; interactive agent not started                                                                  |
| SMTP / email               | Env (`FWP_SMTP_*`)           | 🟡 Ready    | Faculty timetable email implemented; requires `FWP_SMTP_HOST` + `FWP_SMTP_FROM` to send                                                                                |


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

# Re-seed policies after changing designation hours / teaching-load weight
# POST http://localhost:8000/api/v1/policies/seed-aiml

# Start frontend
cd frontend && npm run dev
```

- API docs: [http://localhost:8000/docs](http://localhost:8000/docs)  
- Frontend: [http://localhost:5173](http://localhost:5173)  
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

