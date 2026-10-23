"""Auth0 CIBA gateway: request format, status mapping, polling rules and secret hygiene."""
import json
import re

import pytest

from slothguard.auth.approvals import ApprovalStatus, RemediationAction, RemediationExecutor
from slothguard.auth.ciba import Auth0CibaGateway, Auth0GatewayError, make_binding_message

DOMAIN = "dev-test.us.auth0.com"
SECRET = "super-secret-value"
APPROVER = "auth0|approver123"

ACCEPTED = (200, {"auth_req_id": "req-1", "expires_in": 120, "interval": 5})
PENDING = (400, {"error": "authorization_pending"})
APPROVED = (200, {"access_token": "SECRET-TOKEN", "token_type": "Bearer", "expires_in": 86400})
DENIED = (400, {"error": "access_denied", "error_description": "denied or expired"})


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class FakePost:
    """Replays answers in order; the last one repeats. An Exception item is raised."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []

    def __call__(self, url, fields):
        self.calls.append((url, dict(fields)))
        item = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        if isinstance(item, Exception):
            raise item
        return item


class FakeRevoker:
    def __init__(self):
        self.calls = []

    def revoke(self, user_id, role):
        self.calls.append((user_id, role))


@pytest.fixture
def action():
    return RemediationAction(kind="revoke_role", user_id="U001", role="Payment_Release", rule_id="SOD-001")


def make(post, clock=None, **kwargs):
    return Auth0CibaGateway(domain=DOMAIN, client_id="cid", client_secret=SECRET,
                            approver_user_id=APPROVER, post=post, clock=clock or FakeClock(), **kwargs)


# ---- the request ----

def test_request_goes_to_bc_authorize_with_the_documented_fields(action):
    post = FakePost(ACCEPTED)
    make(post).request_approval(action)
    url, fields = post.calls[0]
    assert url == f"https://{DOMAIN}/bc-authorize"
    assert fields["client_id"] == "cid"
    assert fields["client_secret"] == SECRET
    assert fields["scope"] == "openid"
    assert fields["requested_expiry"] == "120"
    assert json.loads(fields["login_hint"]) == {"format": "iss_sub", "iss": f"https://{DOMAIN}/", "sub": APPROVER}
    assert fields["binding_message"] == make_binding_message(action)


def test_request_returns_the_auth_req_id_as_request_id(action):
    assert make(FakePost(ACCEPTED)).request_approval(action) == "req-1"


def test_domain_may_be_given_with_scheme_and_trailing_slash(action):
    post = FakePost(ACCEPTED)
    Auth0CibaGateway(domain=f"https://{DOMAIN}/", client_id="cid", client_secret=SECRET,
                     approver_user_id=APPROVER, post=post, clock=FakeClock()).request_approval(action)
    assert post.calls[0][0] == f"https://{DOMAIN}/bc-authorize"


@pytest.mark.parametrize("role, user", [("Payment_Release", "U001"), ("Pay ment/Release!", "U 002"), ("R" * 80, "U" * 80)])
def test_binding_message_uses_only_allowed_characters_and_at_most_64_of_them(role, user):
    message = make_binding_message(RemediationAction("revoke_role", user, role, "SOD-001"))
    assert re.fullmatch(r"[A-Za-z0-9+\-_.,:#]+", message)
    assert len(message) <= 64


@pytest.mark.parametrize("expiry", [0, -1, 301, 3600])
def test_requested_expiry_must_stay_within_the_push_channel_limit(expiry):
    with pytest.raises(ValueError):
        make(FakePost(ACCEPTED), requested_expiry=expiry)


def test_a_rejected_request_raises_without_leaking_the_secret(action):
    post = FakePost((401, {"error": "access_denied", "error_description": "Unauthorized"}))
    with pytest.raises(Auth0GatewayError) as caught:
        make(post).request_approval(action)
    assert "access_denied" in str(caught.value)
    assert SECRET not in str(caught.value)


def test_a_transport_failure_is_reported_as_a_gateway_error(action):
    with pytest.raises(Auth0GatewayError) as caught:
        make(FakePost(ConnectionError("offline"))).request_approval(action)
    assert SECRET not in str(caught.value)


def test_the_secret_is_not_in_the_repr():
    assert SECRET not in repr(make(FakePost(ACCEPTED)))


# ---- polling and status mapping ----

def test_status_is_pending_before_the_first_polling_interval_and_makes_no_call(action):
    post = FakePost(ACCEPTED, APPROVED)
    gateway = make(post)
    request_id = gateway.request_approval(action)
    assert gateway.get_status(request_id) is ApprovalStatus.PENDING
    assert len(post.calls) == 1  # only bc-authorize


def test_pending_then_approved_following_the_interval(action):
    clock, post = FakeClock(), FakePost(ACCEPTED, PENDING, APPROVED)
    gateway = make(post, clock)
    request_id = gateway.request_approval(action)
    clock.advance(5)
    assert gateway.get_status(request_id) is ApprovalStatus.PENDING
    assert gateway.get_status(request_id) is ApprovalStatus.PENDING  # same instant: no new call
    assert len(post.calls) == 2
    clock.advance(5)
    assert gateway.get_status(request_id) is ApprovalStatus.APPROVED


def test_the_token_request_uses_the_ciba_grant(action):
    clock, post = FakeClock(), FakePost(ACCEPTED, PENDING)
    gateway = make(post, clock)
    request_id = gateway.request_approval(action)
    clock.advance(5)
    gateway.get_status(request_id)
    url, fields = post.calls[1]
    assert url == f"https://{DOMAIN}/oauth/token"
    assert fields["grant_type"] == "urn:openid:params:grant-type:ciba"
    assert fields["auth_req_id"] == "req-1"
    assert fields["client_id"] == "cid" and fields["client_secret"] == SECRET


def test_approved_is_final_and_the_token_is_not_kept(action):
    clock, post = FakeClock(), FakePost(ACCEPTED, APPROVED)
    gateway = make(post, clock)
    request_id = gateway.request_approval(action)
    clock.advance(5)
    assert gateway.get_status(request_id) is ApprovalStatus.APPROVED
    clock.advance(60)
    assert gateway.get_status(request_id) is ApprovalStatus.APPROVED
    assert len(post.calls) == 2
    assert "SECRET-TOKEN" not in repr(vars(gateway))


def test_access_denied_before_the_deadline_is_denied(action):
    clock, post = FakeClock(), FakePost(ACCEPTED, DENIED)
    gateway = make(post, clock)
    request_id = gateway.request_approval(action)
    clock.advance(5)
    assert gateway.get_status(request_id) is ApprovalStatus.DENIED


def test_the_local_clock_decides_expiry_without_calling_auth0(action):
    clock, post = FakeClock(), FakePost(ACCEPTED, PENDING)
    gateway = make(post, clock)
    request_id = gateway.request_approval(action)
    clock.advance(120)
    assert gateway.get_status(request_id) is ApprovalStatus.EXPIRED
    assert len(post.calls) == 1


def test_slow_down_lengthens_the_interval(action):
    clock = FakeClock()
    post = FakePost(ACCEPTED, (400, {"error": "slow_down", "interval": 10}), APPROVED)
    gateway = make(post, clock)
    request_id = gateway.request_approval(action)
    clock.advance(5)
    assert gateway.get_status(request_id) is ApprovalStatus.PENDING   # slow_down
    clock.advance(9)
    assert gateway.get_status(request_id) is ApprovalStatus.PENDING   # still inside the new interval
    assert len(post.calls) == 2
    clock.advance(1)
    assert gateway.get_status(request_id) is ApprovalStatus.APPROVED


def test_an_unknown_request_id_is_an_error():
    with pytest.raises(Auth0GatewayError):
        make(FakePost(ACCEPTED)).get_status("never-issued")


def test_an_unexpected_error_code_fails_closed(action):
    clock, post = FakeClock(), FakePost(ACCEPTED, (401, {"error": "invalid_client"}))
    gateway = make(post, clock)
    request_id = gateway.request_approval(action)
    clock.advance(5)
    with pytest.raises(Auth0GatewayError):
        gateway.get_status(request_id)


def test_a_transport_failure_while_polling_is_a_gateway_error(action):
    clock, post = FakeClock(), FakePost(ACCEPTED, TimeoutError("slow"))
    gateway = make(post, clock)
    request_id = gateway.request_approval(action)
    clock.advance(5)
    with pytest.raises(Auth0GatewayError):
        gateway.get_status(request_id)


# ---- configuration from the environment ----

def test_from_env_builds_a_working_gateway(action):
    env = {"AUTH0_DOMAIN": DOMAIN, "AUTH0_CLIENT_ID": "cid", "AUTH0_CLIENT_SECRET": SECRET, "AUTH0_TEST_USER_ID": APPROVER}
    post = FakePost(ACCEPTED)
    Auth0CibaGateway.from_env(env, post=post, clock=FakeClock()).request_approval(action)
    assert post.calls[0][1]["client_id"] == "cid"


def test_from_env_names_missing_values_without_printing_the_others():
    env = {"AUTH0_DOMAIN": DOMAIN, "AUTH0_CLIENT_ID": "cid", "AUTH0_TEST_USER_ID": APPROVER}
    with pytest.raises(ValueError) as caught:
        Auth0CibaGateway.from_env(env)
    assert "AUTH0_CLIENT_SECRET" in str(caught.value)
    assert "cid" not in str(caught.value) and DOMAIN not in str(caught.value)


# ---- together with the human-approval gate ----

def test_approved_request_lets_the_executor_revoke_once(action):
    clock, post, revoker = FakeClock(), FakePost(ACCEPTED, APPROVED), FakeRevoker()
    executor = RemediationExecutor(make(post, clock), revoker)
    pending = executor.propose(action)
    clock.advance(5)
    assert executor.execute(pending) == "executed"
    assert revoker.calls == [("U001", "Payment_Release")]


def test_denied_request_never_revokes(action):
    clock, post, revoker = FakeClock(), FakePost(ACCEPTED, DENIED), FakeRevoker()
    executor = RemediationExecutor(make(post, clock), revoker)
    pending = executor.propose(action)
    clock.advance(5)
    assert executor.execute(pending) == "denied"
    assert revoker.calls == []


def test_an_early_execute_waits_and_revokes_nothing(action):
    revoker = FakeRevoker()
    executor = RemediationExecutor(make(FakePost(ACCEPTED, APPROVED)), revoker)
    pending = executor.propose(action)
    assert executor.execute(pending) == "waiting"
    assert revoker.calls == []


def test_an_expired_request_never_revokes(action):
    clock, revoker = FakeClock(), FakeRevoker()
    executor = RemediationExecutor(make(FakePost(ACCEPTED, PENDING), clock), revoker)
    pending = executor.propose(action)
    clock.advance(200)
    assert executor.execute(pending) == "expired"
    assert revoker.calls == []


def test_a_gateway_failure_fails_closed(action):
    clock, revoker = FakeClock(), FakeRevoker()
    executor = RemediationExecutor(make(FakePost(ACCEPTED, ConnectionError("offline")), clock), revoker)
    pending = executor.propose(action)
    clock.advance(5)
    assert executor.execute(pending) == "error"
    assert revoker.calls == []
