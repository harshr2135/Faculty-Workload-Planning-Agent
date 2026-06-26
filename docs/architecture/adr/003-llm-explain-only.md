# ADR 003: LLM Explain-Only Policy

## Status

Accepted

## Context

Stakeholders require explainability and trust. LLMs are unsuitable for hard constraint satisfaction.

## Decision

LLM layer reads optimization output and explains it. It never produces authoritative allocations.

## Consequences

- Allocation success does not depend on AI availability
- Prompt guardrails required in `backend/ai/prompts/guardrails/`
