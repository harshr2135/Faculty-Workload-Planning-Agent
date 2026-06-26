# Optimization Engine

Deterministic workload allocation using Google OR-Tools CP-SAT.

**Fully isolated** — no imports from `ai/`, `api/`, or LangChain.

## Submodules

- `engine/` — Solver factory and CP-SAT implementation
- `constraints/` — Teaching hours, AICTE rules, specialization, timetable
- `objectives/` — Fairness, preferences, workload balance
- `preprocessing/` — Problem builder, conflict detector
- `postprocessing/` — Solution validator, explainability payload
- `strategies/` — Standard allocation, emergency substitution

## Output

Structured `OptimizationSolution` consumed by services, reports, and AI layer.
