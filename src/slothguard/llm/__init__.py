"""Explanations of SoD findings, written by a local model.

The rules decide what is a finding and how severe it is. The model only explains.
If the model fails, answers nothing, or breaks the sentence limit, a deterministic
template is used instead, so the report is never blocked by the model.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Protocol

from slothguard.models import Finding, SoDRule

MAX_SENTENCES = 4

# A sentence ends at . ! or ? followed by whitespace and a capital letter, a digit,
# a quote or an opening bracket. This keeps "e.g. approvals" and "3.5" in one piece.
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")


class LLMClient(Protocol):
    def generate(self, prompt: str) -> str: ...


@dataclass(frozen=True)
class Explanation:
    text: str
    source: str  # "model", "cache" or "fallback"


class ExplanationCache:
    """In-memory cache keyed by (rule id, user id). Only model answers are stored."""

    def __init__(self) -> None:
        self._data: dict[tuple[str, str], str] = {}

    def get(self, finding: Finding) -> Optional[str]:
        return self._data.get((finding.rule_id, finding.user_id))

    def put(self, finding: Finding, text: str) -> None:
        self._data[(finding.rule_id, finding.user_id)] = text


def count_sentences(text: str) -> int:
    stripped = text.strip()
    if not stripped:
        return 0
    return len([part for part in _SENTENCE_BREAK.split(stripped) if part.strip()])


def build_prompt(finding: Finding, rule: SoDRule, max_sentences: int = MAX_SENTENCES) -> str:
    first, second = finding.roles
    return (
        "You are assisting a GRC analyst reviewing access rights.\n"
        f"Rule: {rule.name} ({rule.id}). Severity: {finding.severity}.\n"
        f"User: {finding.user_id}. Conflicting roles held: {first} and {second}.\n"
        f"Rule description: {rule.description}\n"
        f"Explain in no more than {max_sentences} sentences why holding both roles is a risk "
        "and what to review. Do not change the severity."
    )


def fallback_text(finding: Finding, rule: SoDRule) -> str:
    first, second = finding.roles
    return (
        f"User {finding.user_id} holds both '{first}' and '{second}', which conflicts with "
        f"rule {rule.id} ({rule.name}). Severity: {finding.severity}. "
        "Review whether both roles are needed."
    )


def explain_finding(
    finding: Finding,
    rule: SoDRule,
    client: LLMClient,
    cache: Optional[ExplanationCache] = None,
    max_sentences: int = MAX_SENTENCES,
) -> Explanation:
    if cache is not None:
        hit = cache.get(finding)
        if hit:
            return Explanation(text=hit, source="cache")

    try:
        answer = client.generate(build_prompt(finding, rule, max_sentences))
    except Exception:
        return Explanation(text=fallback_text(finding, rule), source="fallback")

    if not isinstance(answer, str) or not answer.strip():
        return Explanation(text=fallback_text(finding, rule), source="fallback")

    text = answer.strip()
    if count_sentences(text) > max_sentences:
        return Explanation(text=fallback_text(finding, rule), source="fallback")

    if cache is not None:
        cache.put(finding, text)
    return Explanation(text=text, source="model")
