"""Minimal async LLM client for explain-only narrative generation."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Literal

import httpx
import yaml

from backend.config.settings import get_settings

logger = logging.getLogger(__name__)

_CONFIG_PATH = Path(__file__).resolve().parents[3] / "configs" / "ai_providers.yaml"
_REPORT_STRUCTURE_PATH = (
    Path(__file__).resolve().parents[1] / "prompts" / "batch_report_structure.md"
)

FullReportMode = Literal["facts", "raw"]


def _load_provider_config() -> dict[str, Any]:
    if not _CONFIG_PATH.is_file():
        return {"default_provider": "nim", "providers": {}}
    with _CONFIG_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _load_report_structure_prompt() -> str:
    if _REPORT_STRUCTURE_PATH.is_file():
        return _REPORT_STRUCTURE_PATH.read_text(encoding="utf-8")
    return (
        "Write a markdown department workload report using only the JSON facts provided. "
        "Do not invent numbers or names."
    )


def ai_narrative_available() -> bool:
    settings = get_settings()
    if not settings.fwp_ai_enabled:
        return False
    config = _load_provider_config()
    provider_name = settings.fwp_ai_provider or config.get("default_provider", "nim")
    providers = config.get("providers", {})
    provider = providers.get(provider_name, {})
    api_key_env = provider.get("api_key_env", "")
    return bool(_resolve_secret(api_key_env, settings))


def _resolve_secret(env_key: str, settings: Any) -> str | None:
    mapping = {
        "FWP_NIM_API_KEY": settings.fwp_nim_api_key,
        "FWP_OPENAI_API_KEY": settings.fwp_openai_api_key,
        "FWP_GROQ_API_KEY": settings.fwp_groq_api_key,
    }
    value = mapping.get(env_key)
    return value.strip() if value else None


def _strip_markdown_fences(content: str) -> str:
    trimmed = content.strip()
    fence_match = re.match(r"^```(?:markdown|md)?\s*\n?(.*?)\n?```\s*$", trimmed, re.DOTALL)
    if fence_match:
        return fence_match.group(1).strip()
    return trimmed


async def _invoke_llm(system_prompt: str, user_prompt: str, *, max_tokens: int) -> str | None:
    settings = get_settings()
    if not settings.fwp_ai_enabled:
        return None

    config = _load_provider_config()
    provider_name = settings.fwp_ai_provider or config.get("default_provider", "nim")
    providers = config.get("providers", {})
    provider = providers.get(provider_name)
    if not provider:
        logger.warning("Unknown AI provider '%s'", provider_name)
        return None

    api_key = _resolve_secret(provider.get("api_key_env", ""), settings)
    if not api_key:
        return None

    model = provider.get("model", "gpt-4o-mini")

    try:
        if provider_name == "openai":
            content = await _chat_openai_compatible(
                "https://api.openai.com/v1",
                api_key,
                model,
                system_prompt,
                user_prompt,
                max_tokens=max_tokens,
            )
        elif provider_name == "groq":
            content = await _chat_openai_compatible(
                "https://api.groq.com/openai/v1",
                api_key,
                model,
                system_prompt,
                user_prompt,
                max_tokens=max_tokens,
            )
        else:
            base_url = settings.fwp_nim_base_url or "https://integrate.api.nvidia.com/v1"
            content = await _chat_openai_compatible(
                base_url.rstrip("/"),
                api_key,
                model,
                system_prompt,
                user_prompt,
                max_tokens=max_tokens,
            )
        return _strip_markdown_fences(content) if content else None
    except Exception:
        logger.exception("LLM request failed")
        return None


async def generate_executive_summary(facts_json: str) -> str | None:
    """Return an LLM-written executive summary, or None if AI is unavailable."""
    system_prompt = (
        "You write concise executive summaries for university department heads reviewing "
        "faculty workload allocation plans. Use only the facts provided in JSON. "
        "Do not invent faculty names, course codes, or numbers. "
        "Write 1 short paragraph (4-6 sentences) in professional academic tone. "
        "Mention workload spread, PEC electives, lab coverage, and any policy warnings if present."
    )
    user_prompt = (
        "Write an executive summary paragraph for this batch allocation report:\n\n"
        f"{facts_json}"
    )
    return await _invoke_llm(system_prompt, user_prompt, max_tokens=500)


async def generate_full_report_markdown(
    payload_json: str,
    *,
    mode: FullReportMode,
    generated_at: str,
) -> str | None:
    """Return a full markdown report from facts (A) or raw slice JSON (B)."""
    structure_prompt = _load_report_structure_prompt()
    if mode == "facts":
        data_label = "aggregated report facts"
        extra = (
            "The JSON contains pre-computed counts and table rows (pec_rows, faculty_rows). "
            "Render tables directly from those arrays; do not recalculate aggregates."
        )
    else:
        data_label = "raw allocation slice"
        extra = (
            "The JSON contains raw assignments, timetable entries, pec_enrollments, and "
            "faculty summaries. You must derive counts, PEC pool groupings, scheduled status, "
            "and faculty workload tables from this data."
        )

    system_prompt = f"{structure_prompt}\n\n## Data mode\n\n{extra}"
    user_prompt = (
        f"Generate the complete department workload report for this {data_label}.\n"
        f"Use this timestamp for the **Generated:** line: {generated_at}\n\n"
        f"{payload_json}"
    )
    return await _invoke_llm(system_prompt, user_prompt, max_tokens=4096)


async def _chat_openai_compatible(
    base_url: str,
    api_key: str,
    model: str,
    system: str,
    user: str,
    *,
    max_tokens: int = 500,
) -> str | None:
    url = f"{base_url}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices") or []
        if not choices:
            return None
        content = choices[0].get("message", {}).get("content")
        return content.strip() if isinstance(content, str) and content.strip() else None
