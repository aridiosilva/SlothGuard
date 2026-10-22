"""Human-in-the-loop gate: nothing is revoked without an explicit approval. Fail closed."""
import pytest

from slothguard.auth.approvals import (
    ApprovalStatus,
    RemediationAction,
    RemediationExecutor,
)


class FakeGateway:
    """Stands in for the Auth0 asynchronous authorization (CIBA) adapter."""

    def __init__(self, statuses, request_id="req-1"):
        self.statuses = list(statuses)
        self.request_id = request_id
        self.requested = []

    def request_approval(self, action):
        self.requested.append(action)
        return self.request_id

    def get_status(self, request_id):
        assert request_id == self.request_id
        value = self.statuses.pop(0) if len(self.statuses) > 1 else self.statuses[0]
        if isinstance(value, Exception):
            raise value
        return value


class FakeRevoker:
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def revoke(self, user_id, role):
        if self.error:
            raise self.error
        self.calls.append((user_id, role))


@pytest.fixture
def action():
    return RemediationAction(kind="revoke_role", user_id="U001",
                             role="Payment_Release", rule_id="R1")


def _executor(statuses, revoker=None):
    gateway = FakeGateway(statuses)
    revoker = revoker or FakeRevoker()
    return RemediationExecutor(gateway, revoker), gateway, revoker


def test_propose_asks_for_approval_and_does_not_revoke(action):
    executor, gateway, revoker = _executor([ApprovalStatus.PENDING])
    pending = executor.propose(action)
    assert gateway.requested == [action]
    assert pending.request_id == "req-1"
    assert pending.action == action
    assert revoker.calls == []


def test_pending_approval_does_not_revoke(action):
    executor, _, revoker = _executor([ApprovalStatus.PENDING])
    pending = executor.propose(action)
    assert executor.execute(pending) == "waiting"
    assert revoker.calls == []


def test_denied_approval_does_not_revoke(action):
    executor, _, revoker = _executor([ApprovalStatus.DENIED])
    pending = executor.propose(action)
    assert executor.execute(pending) == "denied"
    assert revoker.calls == []


def test_expired_approval_does_not_revoke(action):
    executor, _, revoker = _executor([ApprovalStatus.EXPIRED])
    pending = executor.propose(action)
    assert executor.execute(pending) == "expired"
    assert revoker.calls == []


def test_approved_revokes_exactly_the_requested_role(action):
    executor, _, revoker = _executor([ApprovalStatus.APPROVED])
    pending = executor.propose(action)
    assert executor.execute(pending) == "executed"
    assert revoker.calls == [("U001", "Payment_Release")]


def test_executing_twice_revokes_only_once(action):
    executor, _, revoker = _executor([ApprovalStatus.APPROVED])
    pending = executor.propose(action)
    assert executor.execute(pending) == "executed"
    assert executor.execute(pending) == "already_executed"
    assert len(revoker.calls) == 1


def test_waiting_then_approved_revokes_on_the_later_call(action):
    executor, _, revoker = _executor([ApprovalStatus.PENDING, ApprovalStatus.APPROVED])
    pending = executor.propose(action)
    assert executor.execute(pending) == "waiting"
    assert revoker.calls == []
    assert executor.execute(pending) == "executed"
    assert revoker.calls == [("U001", "Payment_Release")]


def test_gateway_error_fails_closed(action):
    executor, _, revoker = _executor([RuntimeError("auth0 unreachable")])
    pending = executor.propose(action)
    assert executor.execute(pending) == "error"
    assert revoker.calls == []


def test_revoker_error_is_reported_and_not_logged_as_executed(action):
    executor, _, _ = _executor([ApprovalStatus.APPROVED],
                               revoker=FakeRevoker(error=RuntimeError("directory down")))
    pending = executor.propose(action)
    assert executor.execute(pending) == "error"
    events = [entry.event for entry in executor.audit]
    assert "error" in events
    assert "executed" not in events


def test_only_revoke_role_actions_are_supported(action):
    executor, gateway, revoker = _executor([ApprovalStatus.APPROVED])
    risky = RemediationAction(kind="delete_user", user_id="U001", role="", rule_id="R1")
    with pytest.raises(ValueError):
        executor.propose(risky)
    assert gateway.requested == []
    assert revoker.calls == []


def test_audit_trail_for_the_happy_path(action):
    executor, _, _ = _executor([ApprovalStatus.APPROVED])
    pending = executor.propose(action)
    executor.execute(pending)
    assert [entry.event for entry in executor.audit] == ["proposed", "approved", "executed"]
    assert {entry.request_id for entry in executor.audit} == {"req-1"}
    assert {(entry.user_id, entry.role) for entry in executor.audit} == {("U001", "Payment_Release")}


def test_audit_trail_records_a_denial(action):
    executor, _, _ = _executor([ApprovalStatus.DENIED])
    pending = executor.propose(action)
    executor.execute(pending)
    assert [entry.event for entry in executor.audit] == ["proposed", "denied"]
