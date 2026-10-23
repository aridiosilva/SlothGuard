"""Simulated side effect of an approved revocation: roles are removed from an in-memory copy.

Nothing outside the running program is changed. The original users are never mutated.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from slothguard.models import UserAccess


def _normalize(role: str) -> str:
    return role.strip().casefold()


class InMemoryRoleRevoker:
    def __init__(self, users: Iterable[UserAccess]) -> None:
        self._users: dict[str, UserAccess] = {user.user_id: user for user in users}

    def users(self) -> list[UserAccess]:
        return list(self._users.values())

    def revoke(self, user_id: str, role: str) -> None:
        user = self._users.get(user_id)
        if user is None:
            raise ValueError(f"unknown user {user_id!r}")
        remaining = frozenset(held for held in user.roles if _normalize(held) != _normalize(role))
        if remaining == user.roles:
            raise ValueError(f"user {user_id!r} does not hold role {role!r}")
        self._users[user_id] = replace(user, roles=remaining)
