# Faculty Workload Planning Agent — Project In & Out Guide

> A plain-language walkthrough of **what this system does**, **what goes in and what comes out**, and **why each technology exists**.  
> Audience: teammates, reviewers, and NVIDIA Capstone evaluators.

---

## 1. What this project is (and is not)

### Purpose

This is an **enterprise decision-support system** for department administrators (e.g. AIML HOD) to:

- Assign **theory** and **laboratory** courses to faculty
- Respect **AICTE / institutional workload limits** by designation
- Build a **weekly timetable** (day, period, room)
- Produce **explainable reports** for review and approval

It is **not** a chatbot that invents allocations. Optimization is done by a **deterministic solver**; the LLM only **explains** and **documents** results.

### Primary stakeholder input

Business rules come from stakeholder survey answers in `InitialSurvey-Ans.docx` (current process, hour limits, lab rules, fairness, trust, and reporting needs). Policies are stored as **configurable data**, not hardcoded magic numbers.

---

## 2. High-level picture

```
┌─────────────────────────────────────────────────────────────────┐
│                     ADMIN (React UI)                            │
│  Faculty · Courses · Rooms · Labs · Policies · Allocations      │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP / JSON (REST)
┌────────────────────────────▼────────────────────────────────────┐
│                     API (FastAPI)                               │
│  Thin controllers → Services → DB / Optimizer / AI reports      │
└──────┬─────────────────┬─────────────────────┬──────────────────┘
       │                 │                     │
       ▼                 ▼                     ▼
  PostgreSQL        OR-Tools CP-SAT         LLM (NIM / OpenAI / Groq)
  (master data,     (workload +             (explain & write reports
   saved plans)      timetable)              — never allocate)
       ▲
       │
     Redis (cache / future jobs — provisioned in Docker)
```

**Golden rule:** *Optimization ≠ AI.* CP-SAT decides who teaches what and when. The LLM only narrates grounded facts.

---

## 3. What goes IN (inputs)

| Input | Where it lives | Why it matters |
|-------|----------------|----------------|
| **Faculty roster** | Excel import → `faculty_members` + specializations | Who can teach; designation drives hour caps |
| **Courses / subjects** | Excel (`Courses.xlsx`) → `courses` | What must be taught (IPCC, PCC, PEC, SEC, labs, etc.) |
| **Student batches & sections** | Seeded / DB | Which years/sections exist (e.g. 2nd–4th year AIML) |
| **Classrooms, labs, lecture halls** | Seeded master data | Where sessions can be placed |
| **Daily time slots** | Seeded timetable config | When teaching happens (periods, break, lunch) |
| **Workload policies** | `designation_workload_policies`, `planning_policies` | AICTE max hours, lab dual-faculty, matching rules |
| **PEC enrollments** | UI / run request | Electives with students > 0 enter the plan; room type by headcount |
| **Run options** | Allocation page | Which batches/semesters to plan; save/load named plans |

### Typical admin preparation flow

1. Start Postgres (+ Redis) via Docker Compose  
2. Seed AIML master data (years, rooms, labs, slots, policies)  
3. Import faculty Excel and courses Excel  
4. Open Allocations → pick batches / semesters → set PEC counts if needed  
5. Run allocation → review grids → edit if needed → save → generate report  

---

## 4. What happens INSIDE (processing pipeline)

When the admin clicks **Run allocation**, the backend roughly does this:

```
1. Load master data + policies from PostgreSQL
2. PREPROCESS
   - Build theory / lab / PEC-SEC slots
   - Split labs into mandatory B1 + B2 sub-batches
   - Match faculty to courses via specialization similarity
   - Fallback: Assistant Professors if no specialist match
3. WORKLOAD SOLVE (default: Google OR-Tools CP-SAT)
   - Hard: weekly hour caps by designation
   - Soft: lab session preferences, fairness / utilization balance
   - Lexicographic: teaching-fit quality dominates load balancing
   - Fallback: greedy allocator if CP-SAT path fails
4. TIMETABLE SOLVE
   - Place sessions on (day, period block, room)
   - Avoid faculty / room / section clashes
   - Continuous lab blocks (no lunch crossing)
   - PEC/SEC → lecture halls or classrooms by enrollment rules
5. POSTPROCESS
   - Validate against policies; collect warnings / violations
   - Persist solution on `allocation_runs`
6. (Optional) REPORT
   - Aggregate facts (deterministic)
   - LLM renders narrative markdown from those facts only
```

### Important domain rules (already implemented)

- **Hard max teaching hours** per designation (cannot exceed)  
- **Two faculty per lab session**  
- **Lab B1 and B2** both mandatory; capacity ~35 per sub-batch  
- **Semester-fixed weekly grid** (same pattern every week)  
- **PEC room rule:** >150 students → lecture hall; ≤150 → classroom; SEC always LH  
- **Roomless** courses (e.g. UG Research Project) skip room booking  
- **Cap-proportional balancing** so load tracks each role’s capacity fairly  

---

## 5. What comes OUT (outputs)

| Output | Form | Consumer |
|--------|------|----------|
| **Faculty ↔ course assignments** | JSON on allocation run + editable UI table | HOD / planner |
| **Weekly timetable grids** | Section, faculty, classroom, laboratory views | Timetable owners |
| **Policy violations / warnings** | Structured + shown in UI / reports | Audit & adjustment |
| **Fairness / utilization metrics** | In solution & reports | Workload fairness review |
| **Batch summary report** | Markdown (deterministic + optional LLM) | HOD review, print/PDF |
| **All-batches combined report** | Markdown with consolidated faculty table | Department-wide review |
| **Saved named plans** | DB rows (`allocation_runs`) | Compare / reload previous plans |

Manual edits after a run are first-class: reassign faculty, then save — the system supports human-in-the-loop approval, which matches survey trust requirements.

---

## 6. System layers (where code lives)

| Layer | Folder | Responsibility |
|-------|--------|----------------|
| **Frontend** | `frontend/` | Admin UI: master data browsing, run allocations, grids, reports |
| **API** | `backend/api/` | REST endpoints only — no heavy business logic |
| **Services** | `backend/services/` | Orchestration: import, allocate, grids, reports |
| **Domain / core** | `backend/core/` | Pure rules (course types, PEC, lab config, matching) |
| **Optimization** | `backend/optimization/` | CP-SAT / greedy solvers, isolated from LLM |
| **AI** | `backend/ai/` | LLM client, prompts, report narration |
| **Models / DB** | `backend/models/`, `database/` | Schema, sessions, migrations path |
| **Config** | `configs/`, `backend/config/` | Env-tier YAML + settings (`FWP_*`) |
| **Infra** | `infra/`, `docker-compose.yml` | Docker, CI/CD scaffolding |
| **Docs / tests** | `docs/`, `tests/` | ADRs, runbooks, unit/integration tests |

Architecture style: **Clean Architecture** (API thin; domain independent; ports/adapters for DB and LLM). See `docs/architecture/`.

---

## 7. Tech stack — what and why

### 7.1 Backend runtime & API

| Technology | Role | Why this choice |
|------------|------|-----------------|
| **Python 3.10+** | Primary backend language | Strong ecosystem for OR-Tools, data, and LLM SDKs; team-friendly for optimization research |
| **FastAPI** | REST API framework | Async-ready, automatic OpenAPI docs, Pydantic validation — fit for typed enterprise APIs |
| **Uvicorn** | ASGI server | Production-grade async server for FastAPI |
| **Pydantic / pydantic-settings** | Request/response schemas & env config | Fail-fast validation; typed contracts between UI and engine |
| **python-jose / passlib** | Auth primitives (JWT, hashing) | Prepared for JWT + RBAC (planned; not the core of current demos) |
| **structlog** | Structured logging | Auditability and ops-friendly logs for allocation runs |
| **PyYAML** | Config files | Human-editable policies and env tiers under `configs/` |
| **openpyxl** | Excel import | Matches real dept workflow (faculty & courses spreadsheets) |
| **httpx** | HTTP client | Outbound calls to LLM providers |

### 7.2 Data & persistence

| Technology | Role | Why this choice |
|------------|------|-----------------|
| **PostgreSQL 16** | System of record | Relational integrity for faculty, courses, rooms, policies, saved plans; scales to real departments |
| **SQLAlchemy 2 (async) + asyncpg** | ORM / DB access | Typed models, async I/O under FastAPI; portable SQL |
| **Alembic** | Schema migrations | Production evolution of schema (migrations still being hardened vs bootstrap) |
| **Redis 7** | Cache / future job broker | Fast ephemeral store; ready for progress, rate limits, or background workers |

Docker Compose runs Postgres on host port **15432** (avoids clashing with a local Postgres on 5432).

### 7.3 Optimization (the “brain” of allocation)

| Technology | Role | Why this choice |
|------------|------|-----------------|
| **Google OR-Tools CP-SAT** | Constraint solver for workload (and timetable CP-SAT path) | Industry-standard CSP/IP solver: deterministic, auditable, handles hard caps + soft objectives |
| **Greedy allocators / schedulers** | Fallback & multi-batch timetable path | Guarantees a usable plan when pure CP-SAT is slow or infeasible; keeps demos reliable |
| **Custom preprocessing** (`slot_builder`, eligibility, PEC/lab modules) | Domain modeling before solve | Encodes AIML rules (B1/B2, LH vs classroom, specialization matching) in code, not in the LLM |

**ADR:** `docs/architecture/adr/002-ortools-cpsat.md` — LLMs must not perform allocation.

### 7.4 AI explanation layer

| Technology | Role | Why this choice |
|------------|------|-----------------|
| **LangChain** | LLM orchestration | Provider-agnostic chains; prompt pipelines for reports |
| **NVIDIA NIM** (default, Llama 3.1 70B) | Capstone-aligned inference | Fits NVIDIA program; strong instruction model for long structured reports |
| **OpenAI / Groq** (optional) | Alternate providers | Portability and local/dev fallbacks via `configs/ai_providers.yaml` |
| **Versioned prompts** (`backend/ai/prompts/`) | Report structure & guardrails | Reproducible wording; reduce hallucination; cite facts only |

**ADR:** `docs/architecture/adr/003-llm-explain-only.md` — AI reads solver output; never invents assignments. Allocation still works if the LLM is down.

### 7.5 Frontend

| Technology | Role | Why this choice |
|------------|------|-----------------|
| **React 19** | UI library | Component model suits dashboards, grids, and multi-step allocation UX |
| **TypeScript** | Typed frontend | Safer API contracts with FastAPI/Pydantic shapes |
| **Vite** | Build / dev server | Fast local iteration for admin UI |
| **React Router** | Page navigation | Faculty, courses, rooms, policies, allocations, timetable |
| **Tailwind CSS** | Styling | Rapid, consistent enterprise layout without heavy CSS frameworks |
| **react-markdown + remark-gfm** | Report preview | Renders LLM/deterministic markdown reports (tables, headings) in-browser |

### 7.6 Tooling, quality & delivery

| Technology | Role | Why this choice |
|------------|------|-----------------|
| **Docker / Docker Compose** | Local infra | One-command Postgres + Redis; reproducible environments |
| **pytest / pytest-asyncio / coverage** | Automated tests | Constraint and allocation logic must be regression-safe |
| **Ruff / mypy** | Lint & types | Production maintainability for a multi-year codebase |
| **GitHub Actions (CI scaffold)** | Continuous checks | Catch backend breakage early (`infra/ci-cd`) |
| **Makefile / scripts** | Ops convenience | Seed, import, run backend/frontend consistently |

---

## 8. End-to-end example (one sentence → many systems)

> “Allocate Sem 5 AIML for batches X and Y, respect AICTE hours, dual-faculty labs, and give me a report.”

1. **UI** sends `POST /api/v1/allocations/run` with batch/semester choices and PEC counts.  
2. **Service** loads faculty, courses, rooms, slots, policies from **PostgreSQL**.  
3. **Preprocessor** builds eligible faculty pools and teaching slots.  
4. **CP-SAT** assigns courses under hard hour caps and soft fairness.  
5. **Timetable engine** places sessions without clashes.  
6. Result stored; **UI** shows grids and an editable assignment table.  
7. Admin may tweak → **PATCH** save.  
8. **Report API** builds facts; optional **NIM LLM** writes a full markdown narrative for HOD review.

---

## 9. What is done vs still ahead (honest snapshot)

### Working today

- Master data + Excel imports (faculty, courses)  
- Policies, specialization matching, multi-batch allocation  
- CP-SAT workload with hard caps + utilization balancing  
- Weekly timetable grids (section / faculty / room / lab)  
- Save/load plans, manual edits  
- Batch and all-batches LLM-assisted reports  

### Still pending / partial

- Full JWT + RBAC  
- Alembic migration hygiene (vs bootstrap)  
- Hard AICTE **minimum** hours (today mostly warnings)  
- Faculty **subject preference** soft objective  
- Interactive AI advisor chat  
- Polished PDF/Excel export beyond markdown/print  

Living tracker: [`docs/PROJECT_TRACKER.md`](PROJECT_TRACKER.md).

---

## 10. How to talk about this project in one paragraph

The Faculty Workload Planning Agent is a **production-shaped decision-support system**: administrators feed faculty, courses, rooms, and AICTE policies into a **FastAPI + PostgreSQL** backend; **Google OR-Tools CP-SAT** (with greedy fallbacks) computes fair, constraint-respecting allocations and weekly timetables; a **React** admin UI lets planners inspect grids and adjust results; and an **NVIDIA NIM / LangChain** layer turns grounded solver facts into readable reports — without ever letting the LLM replace the optimizer. That separation is intentional: **trust and auditability** for academic workload decisions.

---

## Related docs

| Doc | Content |
|-----|---------|
| [`docs/architecture/overview.md`](architecture/overview.md) | Layered architecture |
| [`docs/architecture/optimization-design.md`](architecture/optimization-design.md) | Solver pipeline & constraints |
| [`docs/architecture/ai-layer-design.md`](architecture/ai-layer-design.md) | Explain-only AI design |
| [`docs/PROJECT_TRACKER.md`](PROJECT_TRACKER.md) | Build status & backlog |
| [`README.md`](../README.md) | Repo entry point |
