"""Load and validate the JSON exports (users and SoD rules).

Invalid content raises ValueError; a missing file raises FileNotFoundError.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from slothguard.models import SEVERITY_RANK, SoDRule, UserAccess


def _load_records(path: str | Path) -> list[dict[str, Any]]:
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, list):
        raise ValueError(f"{path}: expected a JSON list")
    for index, record in enumerate(data):
        if not isinstance(record, dict):
            raise ValueError(f"{path}[{index}]: expected a JSON object")
    return data


def _required_text(record: dict[str, Any], key: str, where: str) -> str:
    value = record.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{where}: '{key}' must be a non-empty string")
    return value


def _optional_text(record: dict[str, Any], key: str, where: str) -> str:
    value = record.get(key, "")
    if not isinstance(value, str):
        raise ValueError(f"{where}: '{key}' must be a string")
    return value


def _role_list(record: dict[str, Any], key: str, where: str) -> list[str]:
    value = record.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{where}: '{key}' must be a list")
    for role in value:
        if not isinstance(role, str) or not role.strip():
            raise ValueError(f"{where}: '{key}' must contain only non-empty strings")
    return value


def load_rules(path: str | Path) -> list[SoDRule]:
    rules: list[SoDRule] = []
    seen_ids: set[str] = set()
    for index, record in enumerate(_load_records(path)):
        where = f"{path}[{index}]"
        rule_id = _required_text(record, "id", where)
        name = _required_text(record, "name", where)
        severity = _required_text(record, "severity", where)
        roles = _role_list(record, "conflicting_roles", where)
        if severity not in SEVERITY_RANK:
            raise ValueError(f"{where}: unknown severity {severity!r}")
        if len(roles) != 2:
            raise ValueError(f"{where}: 'conflicting_roles' must list exactly two roles")
        if roles[0].strip().casefold() == roles[1].strip().casefold():
            raise ValueError(f"{where}: the two conflicting roles must be distinct")
        if rule_id in seen_ids:
            raise ValueError(f"{where}: duplicate rule id {rule_id!r}")
        seen_ids.add(rule_id)
        rules.append(SoDRule(
            id=rule_id,
            name=name,
            conflicting_roles=(roles[0], roles[1]),
            severity=severity,
            description=_optional_text(record, "description", where),
        ))
    return rules


def load_users(path: str | Path) -> list[UserAccess]:
    users: list[UserAccess] = []
    seen_ids: set[str] = set()
    for index, record in enumerate(_load_records(path)):
        where = f"{path}[{index}]"
        user_id = _required_text(record, "user_id", where)
        roles = _role_list(record, "roles", where)
        if user_id in seen_ids:
            raise ValueError(f"{where}: duplicate user id {user_id!r}")
        seen_ids.add(user_id)
        users.append(UserAccess(
            user_id=user_id,
            name=_optional_text(record, "name", where),
            unit=_optional_text(record, "unit", where),
            roles=frozenset(roles),
        ))
    return users
