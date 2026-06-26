# ADR 002: Google OR-Tools CP-SAT for Optimization

## Status

Accepted

## Context

Workload allocation is a constraint satisfaction / integer programming problem with fairness objectives.

## Decision

Use Google OR-Tools CP-SAT as the primary solver. LLMs will not perform allocation.

## Consequences

- Deterministic, explainable, auditable allocations
- Requires structured constraint modeling in `backend/optimization/`
