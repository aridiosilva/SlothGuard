"""Web interface for SlothGuard.

Sign in with Auth0, see the findings (found by rules, explained by a local model), and propose
revoking a role. A proposal only asks for approval: the role is revoked, in memory, when the
Auth0 user approves the request on their phone. Everything else fails closed.
"""
from __future__ import annotations

import functools
import hmac
import secrets
import threading
from dataclasses import dataclass
from typing import Any, Optional

from flask import Flask, redirect, render_template, request, session

from slothguard.auth.approvals import (
    PendingRemediation,
    RemediationAction,
    RemediationExecutor,
)
from slothguard.auth.ciba import make_binding_message
from slothguard.llm import ExplanationCache
from slothguard.models import Finding
from slothguard.revoker import InMemoryRoleRevoker
from slothguard.rules import detect_conflicts
from slothguard.web.auth_base import LoginError


@dataclass
class Proposal:
    id: str
    action: RemediationAction
    pending: PendingRemediation
    binding_message: str
    result: str = "waiting"


class ReviewState:
    """Everything the running app keeps in memory (it resets when the app restarts)."""

    def __init__(self, users, rules, gateway, cache: Optional[ExplanationCache]) -> None:
        self.rules = list(rules)
        self.cache = cache if cache is not None else ExplanationCache()
        self.revoker = InMemoryRoleRevoker(users)
        self.executor = RemediationExecutor(gateway, self.revoker)
        self.proposals: dict[str, Proposal] = {}
        self.lock = threading.Lock()

    def findings(self) -> list[Finding]:
        return detect_conflicts(self.revoker.users(), self.rules)


def create_app(
    *,
    users,
    rules,
    gateway,
    auth: Any,
    cache: Optional[ExplanationCache] = None,
    secret_key: Optional[str] = None,
    base_url: str = "http://localhost:8000",
) -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=secret_key or secrets.token_hex(32),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )
    base = base_url.rstrip("/")
    state = ReviewState(users, rules, gateway, cache)
    app.extensions["slothguard"] = state
    if hasattr(auth, "init_app"):
        auth.init_app(app)

    def error_page(message: str, status: int):
        return render_template("error.html", status=status, message=message), status

    def login_required(view):
        @functools.wraps(view)
        def wrapped(*args, **kwargs):
            if "user" not in session:
                if request.method == "GET":
                    return redirect("/")
                return error_page("Sign in first.", 401)
            return view(*args, **kwargs)

        return wrapped

    def csrf_ok() -> bool:
        sent = request.form.get("csrf_token", "")
        return bool(sent) and hmac.compare_digest(sent, session.get("csrf", ""))

    @app.context_processor
    def inject():
        return {"user": session.get("user"), "csrf_token": session.get("csrf", "")}

    @app.after_request
    def security_headers(response):
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'"
        )
        return response

    # ---- login and logout ----

    @app.get("/")
    def index():
        if "user" not in session:
            return render_template("login.html")
        with state.lock:
            findings = state.findings()
            rows = [{"finding": finding, "explanation": state.cache.get(finding)} for finding in findings]
        counts = {level: sum(1 for f in findings if f.severity == level) for level in ("high", "medium", "low")}
        return render_template("dashboard.html", rows=rows, counts=counts)

    @app.get("/login")
    def login():
        return auth.login_redirect(base + "/callback")

    @app.get("/callback")
    def callback():
        try:
            profile = auth.fetch_user()
        except LoginError as error:
            return error_page(str(error), 400)
        session.clear()
        session["user"] = {
            "sub": str(profile.get("sub", "")),
            "label": str(profile.get("nickname") or profile.get("name") or "user"),
        }
        session["csrf"] = secrets.token_urlsafe(32)
        return redirect("/")

    @app.post("/logout")
    @login_required
    def logout():
        if not csrf_ok():
            return error_page("Invalid or missing form token. Reload the page and try again.", 400)
        session.clear()
        return redirect(auth.logout_url(base + "/"))

    # ---- proposals ----

    @app.post("/proposals")
    @login_required
    def create_proposal():
        if not csrf_ok():
            return error_page("Invalid or missing form token. Reload the page and try again.", 400)
        rule_id = request.form.get("rule_id", "")
        user_id = request.form.get("user_id", "")
        role = request.form.get("role", "")
        with state.lock:
            finding = next((f for f in state.findings()
                            if f.rule_id == rule_id and f.user_id == user_id), None)
            if finding is None or role not in finding.roles:
                return error_page("That finding or role is not valid any more.", 400)
            for existing in state.proposals.values():
                if existing.result == "waiting" and existing.action.user_id == user_id \
                        and existing.action.role == role:
                    return redirect(f"/proposals/{existing.id}")
            action = RemediationAction(kind="revoke_role", user_id=user_id, role=role, rule_id=rule_id)
            try:
                pending = state.executor.propose(action)
            except Exception as error:
                # Gateway errors carry safe messages; for anything else only the type is shown.
                text = str(error) if error.__class__.__name__ == "Auth0GatewayError" else error.__class__.__name__
                return error_page(f"Could not ask for approval: {text}", 502)
            proposal = Proposal(id=secrets.token_urlsafe(8), action=action, pending=pending,
                                binding_message=make_binding_message(action))
            state.proposals[proposal.id] = proposal
        return redirect(f"/proposals/{proposal.id}")

    @app.get("/proposals/<proposal_id>")
    @login_required
    def show_proposal(proposal_id):
        with state.lock:
            proposal = state.proposals.get(proposal_id)
            if proposal is None:
                return error_page("Proposal not found.", 404)
            if proposal.result == "waiting":
                proposal.result = state.executor.execute(proposal.pending)
        return render_template("proposal.html", proposal=proposal)

    @app.get("/audit")
    @login_required
    def audit():
        with state.lock:
            entries = list(state.executor.audit)
        return render_template("audit.html", entries=entries)

    return app
