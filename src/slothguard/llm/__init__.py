"""Explanations of SoD findings, written by a local model.

The rules decide what is a finding and how severe it is. The model only explains.
If the model fails, answers nothing, or breaks the sentence limit, a deterministic
template is used instead, so the report is never blocked by the model.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol

from slothguard.models import Finding, SoDRule
from slothguard.llm.ollama_client import OllamaClient, OllamaError

__all__ = [
    "Explanation",
    "ExplanationCache",
    "LLMClient",
    "MAX_SENTENCES",
    "OllamaClient",
    "OllamaError",
    "build_prompt",
    "clean_model_text",
    "count_sentences",
    "explain_finding",
    "fallback_text",
]

MAX_SENTENCES = 4

# A sentence ends at . ! or ? followed by whitespace and a capital letter, a digit,
# a quote or an opening bracket. This keeps "e.g. approvals" and "3.5" in one piece.
_SENTENCE_BREAK = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")

# Markdown escapes such as \_ and \* that models often add.
_MARKDOWN_ESCAPE = re.compile(r"\\([\\`*_{}\[\]()#+\-.!|>~])")


class LLMClient(Protocol):
    def generate(self, prompt: str) -> str: ...


@dataclass(frozen=True)
class Explanation:
    text: str
    source: str  # "model", "cache" or "fallback"
    reason: str = ""  # why the fallback was used: model_error, empty_answer or too_many_sentences


class ExplanationCache:
    """In-memory cache keyed by (rule id, user id). Only model answers are stored."""

    def __init__(self) -> None:
        self._data: dict[tuple[str, str], str] = {}

    def get(self, finding: Finding) -> Optional[str]:
        return self._data.get((finding.rule_id, finding.user_id))

    def put(self, finding: Finding, text: str) -> None:
        self._data[(finding.rule_id, finding.user_id)] = text

    def save(self, path) -> None:
        """Write the cached model answers to a JSON file (ids and text only)."""
        file = Path(path)
        file.parent.mkdir(parents=True, exist_ok=True)
        entries = [
            {"rule_id": rule_id, "user_id": user_id, "text": text}
            for (rule_id, user_id), text in sorted(self._data.items())
        ]
        file.write_text(json.dumps({"version": 1, "entries": entries}, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path) -> "ExplanationCache":
        """Read a file written by save(). A missing file gives an empty cache."""
        file = Path(path)
        cache = cls()
        if not file.exists():
            return cache
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(f"{file}: not valid JSON") from error
        entries = data.get("entries") if isinstance(data, dict) else None
        if not isinstance(entries, list):
            raise ValueError(f"{file}: expected an object with an 'entries' list")
        for entry in entries:
            if not (isinstance(entry, dict) and all(isinstance(entry.get(k), str)
                                                    for k in ("rule_id", "user_id", "text"))):
                raise ValueError(f"{file}: every entry needs rule_id, user_id and text")
            cache._data[(entry["rule_id"], entry["user_id"])] = clean_model_text(entry["text"])
        return cache


def clean_model_text(text: str) -> str:
    """Remove Markdown decoration from a model answer: escapes (\\_), backticks and bold marks."""
    text = _MARKDOWN_ESCAPE.sub(r"\1", text)
    return text.replace("**", "").replace("`", "").strip()


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
        return Explanation(text=fallback_text(finding, rule), source="fallback", reason="model_error")

    text = clean_model_text(answer) if isinstance(answer, str) else ""
    if not text:
        return Explanation(text=fallback_text(finding, rule), source="fallback", reason="empty_answer")

    if count_sentences(text) > max_sentences:
        return Explanation(text=fallback_text(finding, rule), source="fallback", reason="too_many_sentences")

    if cache is not None:
        cache.put(finding, text)
    return Explanation(text=text, source="model")
