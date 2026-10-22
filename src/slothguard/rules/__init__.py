"""Deterministic segregation-of-duties (SoD) engine.

The rules detect conflicts. No model is involved at this layer.
"""
from __future__ import annotations

from collections.abc import Iterable

from slothguard.models import SEVERITY_RANK, Finding, SoDRule, UserAccess
from slothguard.rules.loaders import load_rules, load_users


def _normalize(role: str) -> str:
    return role.strip().casefold()


def detect_conflicts(users: Iterable[UserAccess], rules: Iterable[SoDRule]) -> list[Finding]:
    """Return one Finding per (user, rule) pair where the user holds both roles.

    Roles are compared ignoring case and surrounding spaces. The result is sorted by
    severity (high first), then user id, then rule id, so it does not depend on input order.
    """
    rule_list = list(rules)
    findings: list[Finding] = []
    for user in users:
        held = {_normalize(role) for role in user.roles}
        for rule in rule_list:
            first, second = rule.conflicting_roles
            if _normalize(first) in held and _normalize(second) in held:
                findings.append(Finding(
                    rule_id=rule.id,
                    user_id=user.user_id,
                    roles=rule.conflicting_roles,
                    severity=rule.severity,
                ))
    findings.sort(key=lambda f: (SEVERITY_RANK[f.severity], f.user_id, f.rule_id))
    return findings


__all__ = ["detect_conflicts", "load_rules", "load_users"]
