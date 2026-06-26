# Faculty Workload Planning Agent — Architecture Overview

## System Purpose

Enterprise decision-support system for allocating faculty workload (theory, labs, research, admin, timetable) using deterministic optimization with AI-assisted explanations.

## Layered Architecture

```
Frontend (React)
       ↓
API Layer (FastAPI) — thin controllers only
       ↓
Services / Use Cases — business orchestration
       ↓
┌──────────────┬──────────────┬──────────────┐
│ Repositories │ Optimization │ AI Layer     │
│ (PostgreSQL) │ (OR-Tools)   │ (Explain)    │
└──────────────┴──────────────┴──────────────┘
```

## Key Principles

1. **Optimization ≠ AI** — CP-SAT solves allocations; LLM explains results only
2. **Clean Architecture** — domain core has no framework dependencies
3. **Policy as data** — AICTE rules and limits stored in database/config
4. **Ports & adapters** — repositories and LLM clients are swappable

## Bounded Contexts

- Authentication & RBAC
- Faculty Management
- Course Management
- Timetable Management
- Workload Allocation (optimization engine)
- AI Explanation Layer
- Reporting & Analytics
- Notifications & Approval Workflow

## Related Documents

- [Clean Architecture](clean-architecture.md)
- [Optimization Design](optimization-design.md)
- [AI Layer Design](ai-layer-design.md)
- [ADRs](adr/)
