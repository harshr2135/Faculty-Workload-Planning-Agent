# Clean Architecture

## Dependency Rule

Dependencies point inward. Inner layers never import from outer layers.

```
api → services → core/use_cases → core/domain
                    ↓
              interfaces (ports)
                    ↓
         repositories / optimization / ai (adapters)
```

## Layer Responsibilities

| Layer | Location | Responsibility |
|-------|----------|----------------|
| API | `backend/api/` | HTTP routing, schema binding |
| Services | `backend/services/` | Transaction boundaries, orchestration |
| Use Cases | `backend/core/use_cases/` | Application-specific business flows |
| Domain | `backend/core/domain/` | Pure entities and value objects |
| Interfaces | `backend/core/interfaces/` | Abstract ports |
| Adapters | `backend/repositories/`, `backend/optimization/`, `backend/ai/` | Concrete implementations |

## Rules

- No business logic in API routes
- No SQLAlchemy models in domain layer
- No FastAPI imports in `optimization/` or `core/domain/`
- No LLM imports in `optimization/`
