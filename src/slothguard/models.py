"""Immutable domain models shared across SlothGuard."""
from __future__ import annotations

from dataclasses import dataclass

# Lower rank means more severe. Used to sort findings.
SEVERITY_RANK: dict[str, int] = {"high": 0, "medium": 1, "low": 2}


@dataclass(frozen=True)
class UserAccess:
    """A user and the roles they currently hold."""

    user_id: str
    name: str
    unit: str
    roles: frozenset[str]


@dataclass(frozen=True)
class SoDRule:
    """Two roles that one person should not hold at the same time."""

    id: str
    name: str
    conflicting_roles: tuple[str, str]
    severity: str
    description: str


@dataclass(frozen=True)
class Finding:
    """A user who holds both roles of a rule."""

    rule_id: str
    user_id: str
    roles: tuple[str, str]
    severity: str
