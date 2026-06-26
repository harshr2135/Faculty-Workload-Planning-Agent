"""Infer course specialization requirements and match faculty by similarity."""

from __future__ import annotations

import re
from dataclasses import dataclass

# Synonym groups — if course name and faculty specialization share a group, it's a match.
SPECIALIZATION_GROUPS: list[frozenset[str]] = [
    frozenset({"machine learning", "ml", "mlops", "data science", "data science & analytics"}),
    frozenset({"deep learning", "dl", "generative ai", "neural network", "neural networks"}),
    frozenset({"artificial intelligence", "ai", "explainable ai", "xai"}),
    frozenset({"natural language processing", "nlp", "language processing"}),
    frozenset({"computer vision", "image processing", "image processing and computer vision"}),
    frozenset({"data structures", "algorithms", "design and analysis of algorithms"}),
    frozenset({"database", "database management", "dbms", "sql"}),
    frozenset({"operating systems", "os", "system software", "compiler design"}),
    frozenset({"computer networks", "networking", "network"}),
    frozenset({"probability", "statistics", "probability and statistics"}),
    frozenset({"discrete mathematics", "graph theory", "discrete mathematics and graph theory"}),
    frozenset({"java", "programming", "full stack", "full stack development", "unix", "shell"}),
    frozenset({"computer organization", "architecture", "computer organization and architecture"}),
    frozenset({"theory of computation", "automata", "computation"}),
    frozenset({"transform", "numerical", "numerical techniques"}),
    frozenset({"innovation", "entrepreneurship"}),
    frozenset({"gpu", "gpu architecture"}),
    frozenset({"human computer", "hci", "human computer interface", "interface"}),
    frozenset({"iot", "internet of things", "biomedical"}),
    frozenset({"reinforcement learning", "agentic ai", "cloud computing"}),
]

TOKEN_SPLIT = re.compile(r"[^a-z0-9&+]+")


def _normalize(text: str) -> str:
    return " ".join(TOKEN_SPLIT.split(text.lower().strip()))


def infer_course_keywords(course_name: str) -> list[str]:
    """Derive searchable specialization keywords from a course title."""
    normalized = _normalize(course_name)
    keywords: set[str] = {normalized}

    for group in SPECIALIZATION_GROUPS:
        for term in group:
            if term in normalized or normalized in term:
                keywords.update(group)
                break

    # Also add significant tokens (length > 2) from the course name.
    for token in normalized.split():
        if len(token) > 2:
            keywords.add(token)

    return sorted(keywords)


def _term_in_group(term: str, group: frozenset[str]) -> bool:
    term = _normalize(term)
    return any(term in g or g in term for g in group)


def specialization_matches_course(
    faculty_specializations: list[str],
    course_name: str,
) -> tuple[bool, list[str]]:
    """
    Return whether any faculty specialization is similar to the course,
    and which matched terms/groups were used.
    """
    course_keywords = infer_course_keywords(course_name)
    matched_reasons: list[str] = []

    for spec in faculty_specializations:
        norm_spec = _normalize(spec)
        for keyword in course_keywords:
            if keyword in norm_spec or norm_spec in keyword:
                matched_reasons.append(f"{spec} ↔ {keyword}")
                break
        else:
            for group in SPECIALIZATION_GROUPS:
                if _term_in_group(norm_spec, group) and any(
                    _term_in_group(kw, group) for kw in course_keywords
                ):
                    matched_reasons.append(f"{spec} ~ group({', '.join(sorted(group)[:3])}…)")
                    break

    return bool(matched_reasons), matched_reasons


@dataclass
class CourseFacultyMatch:
    course_id: int
    course_code: str
    course_name: str
    inferred_keywords: list[str]
    matched_faculty: list[dict[str, object]]
    fallback_required: bool
