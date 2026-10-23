"""The web interface: Auth0 login, the findings list, proposing a revocation that needs
human approval, and the audit trail. Login and approval are replaced by fakes here."""
import pytest
from flask import redirect

from slothguard.auth.approvals import ApprovalStatus
from slothguard.auth.ciba import Auth0GatewayError, make_binding_message
from slothguard.llm import ExplanationCache
from slothguard.models import Finding
from slothguard.web import create_app
from slothguard.web.auth_base import LoginError

BASE = "http://localhost:8000"
IDP_LOGIN = "https://idp.test/authorize"
IDP_LOGOUT = "https://idp.test/logout"


class FakeAuth:
    def __init__(self, user=None, fail=False):
        self.user = user or {"sub": "auth0|tester", "nickname": "tester"}
        self.fail = fail
        self.redirect_uri = None
        self.return_to = None

    def login_redirect(self, redirect_uri):
        self.redirect_uri = redirect_uri
        return redirect(IDP_LOGIN)

    def fetch_user(self):
        if self.fail:
            raise LoginError("login failed")
        return self.user

    def logout_url(self, return_to):
        self.return_to = return_to
        return IDP_LOGOUT


class FakeGateway:
    def __init__(self, statuses=None, error=None):
        self.statuses = list(statuses or [ApprovalStatus.PENDING])
        self.error = error
        self.requested = []

    def request_approval(self, action):
        if self.error:
            raise self.error
        self.requested.append(action)
        return "req-%d" % len(self.requested)

    def get_status(self, request_id):
        value = self.statuses.pop(0) if len(self.statuses) > 1 else self.statuses[0]
        if isinstance(value, Exception):
            raise value
        return value


@pytest.fixture
def users(make_user):
    return [
        make_user("U1", ["Vendor_Maintain", "Payment_Release"]),   # R1, high
        make_user("U2", ["Requester", "Approver"]),                # R2, medium
        make_user("U3", ["Report_Viewer"]),                        # clean
    ]


def build(users, rules, gateway=None, auth=None, cache=None):
    app = create_app(users=users, rules=rules, gateway=gateway or FakeGateway(),
                     auth=auth or FakeAuth(), cache=cache, secret_key="test-secret", base_url=BASE)
    app.testing = True
    return app


def sign_in(client):
    assert client.get("/callback").status_code == 302


def csrf(client):
    with client.session_transaction() as session:
        return session["csrf"]


def propose(client, rule_id="R1", user_id="U1", role="Payment_Release", token=None):
    return client.post("/proposals", data={
        "rule_id": rule_id, "user_id": user_id, "role": role,
        "csrf_token": csrf(client) if token is None else token})


# ---- login ----

def test_the_home_page_offers_sign_in_when_signed_out(users, rules):
    text = build(users, rules).test_client().get("/").get_data(as_text=True)
    assert "Sign in with Auth0" in text
    assert 'data-finding="R1|U1"' not in text


def test_protected_pages_send_a_signed_out_visitor_home(users, rules):
    client = build(users, rules).test_client()
    for path in ("/audit", "/proposals/anything"):
        response = client.get(path)
        assert response.status_code == 302 and response.headers["Location"].endswith("/")
    assert client.post("/proposals", data={}).status_code == 401


def test_login_uses_the_registered_callback_address(users, rules):
    auth = FakeAuth()
    response = build(users, rules, auth=auth).test_client().get("/login")
    assert response.status_code == 302 and response.headers["Location"] == IDP_LOGIN
    assert auth.redirect_uri == BASE + "/callback"


def test_the_callback_signs_the_user_in(users, rules):
    client = build(users, rules).test_client()
    sign_in(client)
    text = client.get("/").get_data(as_text=True)
    assert 'data-finding="R1|U1"' in text
    assert "tester" in text


def test_a_failed_login_does_not_sign_in(users, rules):
    client = build(users, rules, auth=FakeAuth(fail=True)).test_client()
    assert client.get("/callback").status_code == 400
    assert "Sign in with Auth0" in client.get("/").get_data(as_text=True)


def test_signing_out_clears_the_session_and_goes_to_the_provider(users, rules):
    auth = FakeAuth()
    client = build(users, rules, auth=auth).test_client()
    sign_in(client)
    response = client.post("/logout", data={"csrf_token": csrf(client)})
    assert response.status_code == 302 and response.headers["Location"] == IDP_LOGOUT
    assert auth.return_to == BASE + "/"
    assert "Sign in with Auth0" in client.get("/").get_data(as_text=True)


def test_signing_out_needs_the_csrf_token(users, rules):
    client = build(users, rules).test_client()
    sign_in(client)
    assert client.post("/logout", data={"csrf_token": "wrong"}).status_code == 400


# ---- the findings list ----

def test_the_dashboard_lists_findings_with_severity_from_the_rules(users, rules):
    client = build(users, rules).test_client()
    sign_in(client)
    text = client.get("/").get_data(as_text=True)
    assert 'data-finding="R1|U1"' in text and 'data-finding="R2|U2"' in text
    assert 'data-finding="R1|U3"' not in text
    assert "high" in text and "medium" in text


def test_cached_explanations_are_shown_and_missing_ones_are_flagged(users, rules):
    cache = ExplanationCache()
    cache.put(Finding(rule_id="R1", user_id="U1", roles=("Vendor_Maintain", "Payment_Release"), severity="high"),
              "One person could create and pay a vendor.")
    client = build(users, rules, cache=cache).test_client()
    sign_in(client)
    text = client.get("/").get_data(as_text=True)
    assert "One person could create and pay a vendor." in text
    assert "Not generated yet" in text


def test_user_supplied_text_is_escaped(rules, make_user):
    hostile = [make_user("<b>x</b>", ["Vendor_Maintain", "Payment_Release"])]
    client = build(hostile, rules).test_client()
    sign_in(client)
    text = client.get("/").get_data(as_text=True)
    assert "&lt;b&gt;x&lt;/b&gt;" in text
    assert "<b>x</b>" not in text


def test_security_headers_are_set(users, rules):
    response = build(users, rules).test_client().get("/")
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "default-src 'self'" in response.headers["Content-Security-Policy"]


# ---- proposing a revocation ----

def test_a_proposal_needs_a_valid_csrf_token_and_asks_nobody(users, rules):
    gateway = FakeGateway()
    client = build(users, rules, gateway=gateway).test_client()
    sign_in(client)
    assert propose(client, token="wrong").status_code == 400
    assert client.post("/proposals", data={"rule_id": "R1", "user_id": "U1", "role": "Payment_Release"}).status_code == 400
    assert gateway.requested == []


def test_a_valid_proposal_requests_approval_and_shows_the_waiting_page(users, rules):
    gateway = FakeGateway()
    client = build(users, rules, gateway=gateway).test_client()
    sign_in(client)
    response = propose(client)
    assert response.status_code == 302
    assert len(gateway.requested) == 1
    action = gateway.requested[0]
    assert (action.kind, action.user_id, action.role, action.rule_id) == ("revoke_role", "U1", "Payment_Release", "R1")
    page = client.get(response.headers["Location"]).get_data(as_text=True)
    assert "Waiting" in page
    assert make_binding_message(action) in page


def test_a_proposal_for_something_that_is_not_a_finding_is_rejected(users, rules):
    gateway = FakeGateway()
    client = build(users, rules, gateway=gateway).test_client()
    sign_in(client)
    assert propose(client, user_id="U3").status_code == 400                    # no finding for U3
    assert propose(client, role="Report_Viewer").status_code == 400            # not one of the two roles
    assert propose(client, rule_id="NOPE").status_code == 400
    assert gateway.requested == []


def test_a_second_proposal_for_the_same_role_reuses_the_open_one(users, rules):
    gateway = FakeGateway()
    client = build(users, rules, gateway=gateway).test_client()
    sign_in(client)
    first, second = propose(client), propose(client)
    assert first.headers["Location"] == second.headers["Location"]
    assert len(gateway.requested) == 1


def test_an_approved_proposal_revokes_the_role_and_clears_the_finding(users, rules):
    client = build(users, rules, gateway=FakeGateway([ApprovalStatus.APPROVED])).test_client()
    sign_in(client)
    location = propose(client).headers["Location"]
    page = client.get(location).get_data(as_text=True)
    assert "Approved" in page and "revoked" in page
    assert 'data-finding="R1|U1"' not in client.get("/").get_data(as_text=True)
    assert 'data-finding="R2|U2"' in client.get("/").get_data(as_text=True)


def test_a_denied_proposal_keeps_the_finding(users, rules):
    client = build(users, rules, gateway=FakeGateway([ApprovalStatus.DENIED])).test_client()
    sign_in(client)
    page = client.get(propose(client).headers["Location"]).get_data(as_text=True)
    assert "Denied" in page
    assert 'data-finding="R1|U1"' in client.get("/").get_data(as_text=True)


def test_an_expired_proposal_keeps_the_finding(users, rules):
    client = build(users, rules, gateway=FakeGateway([ApprovalStatus.EXPIRED])).test_client()
    sign_in(client)
    page = client.get(propose(client).headers["Location"]).get_data(as_text=True)
    assert "Expired" in page
    assert 'data-finding="R1|U1"' in client.get("/").get_data(as_text=True)


def test_a_gateway_failure_is_shown_as_an_error_and_revokes_nothing(users, rules):
    gateway = FakeGateway(error=Auth0GatewayError("bc-authorize failed (HTTP 403): access_denied"))
    client = build(users, rules, gateway=gateway).test_client()
    sign_in(client)
    response = propose(client)
    assert response.status_code == 502
    assert "bc-authorize failed" in response.get_data(as_text=True)
    assert 'data-finding="R1|U1"' in client.get("/").get_data(as_text=True)


def test_a_status_error_while_waiting_fails_closed(users, rules):
    client = build(users, rules, gateway=FakeGateway([RuntimeError("auth0 down")])).test_client()
    sign_in(client)
    page = client.get(propose(client).headers["Location"]).get_data(as_text=True)
    assert "Error" in page
    assert 'data-finding="R1|U1"' in client.get("/").get_data(as_text=True)


def test_an_unknown_proposal_id_is_not_found(users, rules):
    client = build(users, rules).test_client()
    sign_in(client)
    assert client.get("/proposals/does-not-exist").status_code == 404


# ---- audit trail ----

def test_the_audit_trail_lists_each_step(users, rules):
    client = build(users, rules, gateway=FakeGateway([ApprovalStatus.APPROVED])).test_client()
    sign_in(client)
    client.get(propose(client).headers["Location"])
    text = client.get("/audit").get_data(as_text=True)
    for event in ("proposed", "approved", "executed"):
        assert event in text
    assert "Payment_Release" in text and "U1" in text
