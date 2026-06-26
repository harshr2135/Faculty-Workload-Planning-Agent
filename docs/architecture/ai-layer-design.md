# AI Layer Design

## Purpose

Natural language assistance for administrators. **Does not perform optimization.**

## Capabilities

- Explain allocation decisions
- Summarize conflicts
- Suggest alternatives (advisory only)
- Interpret institutional policies
- Answer administrator questions
- Generate documentation

## Structure

```
backend/ai/
├── llm/          # Provider clients (NIM, OpenAI, Groq)
├── chains/       # LangChain pipelines
├── agents/       # Advisor personas
├── rag/          # Future policy document retrieval
├── prompts/      # Version-controlled templates
└── services/     # Explanation, documentation, Q&A
```

## Guardrails

- Input: structured optimization results only
- Output: must cite constraint IDs; must not invent final assignments
- Failure: AI errors must not block allocation runs
