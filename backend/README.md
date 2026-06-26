# Backend

FastAPI application following Clean Architecture.

## Module Map

| Module | Responsibility |
|--------|----------------|
| `api/` | HTTP routes (thin controllers) |
| `core/` | Domain entities, use cases, ports |
| `services/` | Application service facades |
| `repositories/` | SQLAlchemy data access |
| `models/` | ORM persistence models |
| `schemas/` | Pydantic API DTOs |
| `optimization/` | OR-Tools CP-SAT engine (isolated) |
| `ai/` | LLM explanation layer (isolated) |
| `security/` | JWT, RBAC, password hashing |
| `config/` | Pydantic settings |
| `workers/` | Background jobs (solver, notifications) |

## Rules

- No business logic in `api/`
- `optimization/` must not import `ai/` or FastAPI
- `ai/` must not perform optimization

## Development

```bash
pip install -e "./backend[dev]"
uvicorn backend.main:app --reload
```
