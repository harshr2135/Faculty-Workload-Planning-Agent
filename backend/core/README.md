# Core Layer

Application heart: domain entities, ports (interfaces), and use cases.

## Submodules

- `domain/` — Pure business entities (Faculty, Course, Allocation)
- `interfaces/` — Abstract repository and service contracts
- `use_cases/` — Application-specific business flows
- `events/` — Domain events (allocation completed, approval requested)

No FastAPI, SQLAlchemy, or LangChain imports allowed here.
