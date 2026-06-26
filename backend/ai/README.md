# AI Layer

Natural language assistance — explains optimization results, summarizes conflicts, generates documentation.

**Does not perform optimization.**

## Submodules

- `llm/` — Provider clients (NVIDIA NIM, OpenAI, Groq)
- `chains/` — LangChain pipelines
- `agents/` — Advisor personas
- `rag/` — Future policy document retrieval (FAISS/Chroma)
- `prompts/` — Version-controlled prompt templates and guardrails
- `services/` — Explanation, documentation, policy Q&A

## Input Contract

Reads structured `explainability_payload` from optimization postprocessing only.
