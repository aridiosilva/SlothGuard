"""Human-in-the-loop gate for remediation actions. It fails closed.

Nothing is revoked unless the approval gateway says APPROVED. Any error, expiry or unknown
answer means "do not execute". Every step leaves an audit entry.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class ApprovalStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"


@dataclass(frozen=True)
class RemediationAction:
    kind: str
    user_id: str
    role: str
    rule_id: str


@dataclass(frozen=True)
class PendingRemediation:
    request_id: str
    action: RemediationAction


@dataclass(frozen=True)
class AuditEntry:
    event: str
    request_id: str
    user_id: str
    role: str


class ApprovalGateway(Protocol):
    def request_approval(self, action: RemediationAction) -> str: ...

    def get_status(self, request_id: str) -> ApprovalStatus: ...


class RoleRevoker(Protocol):
    def revoke(self, user_id: str, role: str) -> None: ...


SUPPORTED_KINDS = ("revoke_role",)


class RemediationExecutor:
    def __init__(self, gateway: ApprovalGateway, revoker: RoleRevoker) -> None:
        self._gateway = gateway
        self._revoker = revoker
        self._executed: set[str] = set()
        self.audit: list[AuditEntry] = []

    def _log(self, event: str, pending: PendingRemediation) -> None:
        self.audit.append(
            AuditEntry(event, pending.request_id, pending.action.user_id, pending.action.role)
        )

    def propose(self, action: RemediationAction) -> PendingRemediation:
        if action.kind not in SUPPORTED_KINDS:
            raise ValueError(f"unsupported action kind {action.kind!r}")
        pending = PendingRemediation(self._gateway.request_approval(action), action)
        self._log("proposed", pending)
        return pending

    def execute(self, pending: PendingRemediation) -> str:
        """Return "executed", "already_executed", "waiting", "denied", "expired" or "error"."""
        if pending.request_id in self._executed:
            return "already_executed"
        try:
            status = self._gateway.get_status(pending.request_id)
        except Exception:
            self._log("error", pending)
            return "error"

        if status is ApprovalStatus.PENDING:
            return "waiting"
        if status is ApprovalStatus.DENIED:
            self._log("denied", pending)
            return "denied"
        if status is ApprovalStatus.EXPIRED:
            self._log("expired", pending)
            return "expired"
        if status is not ApprovalStatus.APPROVED:
            self._log("error", pending)
            return "error"

        self._log("approved", pending)
        try:
            self._revoker.revoke(pending.action.user_id, pending.action.role)
        except Exception:
            self._log("error", pending)
            return "error"
        self._executed.add(pending.request_id)
        self._log("executed", pending)
        return "executed"
