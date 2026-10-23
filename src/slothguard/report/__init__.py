"""Markdown report builder: a pure function from findings and explanations to text."""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import date

from slothguard.llm import Explanation
from slothguard.models import Finding

_SEVERITIES = ("high", "medium", "low")


def build_report(
    findings: Sequence[Finding],
    explanations: Mapping[tuple[str, str], Explanation],
    generated_on: date,
) -> str:
    """Build the report. Findings are written in the order given; explanations are looked
    up by (rule id, user id)."""
    lines = [
        "# SoD Review Report",
        "",
        f"Generated on: {generated_on.isoformat()}",
        "",
        "## Summary",
        "",
    ]
    for severity in _SEVERITIES:
        count = sum(1 for finding in findings if finding.severity == severity)
        lines.append(f"- {severity.capitalize()}: {count}")

    if not findings:
        lines += ["", "No SoD conflicts found."]
        return "\n".join(lines) + "\n"

    lines += ["", "## Findings", ""]
    for finding in findings:
        first, second = finding.roles
        lines += [
            f"### {finding.rule_id} | {finding.user_id}",
            f"- Severity: {finding.severity.capitalize()}",
            f"- Roles: {first} + {second}",
        ]
        explanation = explanations.get((finding.rule_id, finding.user_id))
        if explanation is None:
            lines.append("- Explanation not available.")
        else:
            lines += [f"- Source: {explanation.source}", "", explanation.text]
        lines.append("")
    return "\n".join(lines) + "\n"
