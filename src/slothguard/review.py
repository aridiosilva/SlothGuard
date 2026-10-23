"""One full review: detect conflicts with the rules, explain each with the model, build the report.

The rules decide what is a finding and how severe it is. The model only explains, and a failing
model never blocks the report (each finding then gets the fallback text).
"""
from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import date
from typing import Optional

from slothguard.llm import (
    MAX_SENTENCES,
    Explanation,
    ExplanationCache,
    LLMClient,
    explain_finding,
)
from slothguard.models import Finding, SoDRule, UserAccess
from slothguard.report import build_report
from slothguard.rules import detect_conflicts

ProgressCallback = Callable[[int, int, Finding, Explanation], None]


@dataclass(frozen=True)
class ReviewResult:
    findings: list[Finding]
    explanations: dict[tuple[str, str], Explanation]
    report: str
    counts: dict[str, int]  # how many explanations came from "model", "cache" and "fallback"


def run_review(
    users: Iterable[UserAccess],
    rules: Iterable[SoDRule],
    client: LLMClient,
    generated_on: date,
    cache: Optional[ExplanationCache] = None,
    max_sentences: int = MAX_SENTENCES,
    on_progress: Optional[ProgressCallback] = None,
) -> ReviewResult:
    rule_list = list(rules)
    rules_by_id = {rule.id: rule for rule in rule_list}
    findings = detect_conflicts(users, rule_list)

    explanations: dict[tuple[str, str], Explanation] = {}
    counts = {"model": 0, "cache": 0, "fallback": 0}
    for index, finding in enumerate(findings, start=1):
        explanation = explain_finding(
            finding, rules_by_id[finding.rule_id], client, cache=cache, max_sentences=max_sentences
        )
        explanations[(finding.rule_id, finding.user_id)] = explanation
        counts[explanation.source] += 1
        if on_progress is not None:
            on_progress(index, len(findings), finding, explanation)

    report = build_report(findings, explanations, generated_on)
    return ReviewResult(findings=findings, explanations=explanations, report=report, counts=counts)
