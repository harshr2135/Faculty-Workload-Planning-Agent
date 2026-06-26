# ADR 001: Clean Architecture

## Status

Accepted

## Context

Enterprise decision-support system requiring maintainability, testability, and future microservice extraction.

## Decision

Adopt Clean Architecture with explicit ports and adapters. API layer contains no business logic.

## Consequences

- More initial structure, but clear boundaries
- Optimization and AI modules can be extracted to separate services later
