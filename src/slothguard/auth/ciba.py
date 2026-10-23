"""Auth0 CIBA gateway: asks a human to approve an action on their phone (Auth0 Guardian push).

It implements the ApprovalGateway of slothguard.auth.approvals:
    request_approval(action) -> request_id
    get_status(request_id)   -> ApprovalStatus

Facts it relies on, from the Auth0 documentation and the manual test of 2026-10-23:
- POST /bc-authorize with login_hint {"format": "iss_sub", ...}, scope openid, a binding_message
  (required, at most 64 characters, only alphanumerics and +-_.,:#) and requested_expiry.
- A requested_expiry of at most 300 s uses the push channel.
- POST /oauth/token with the CIBA grant, about every 5 s; "authorization_pending" while waiting,
  "slow_down" asks for a longer interval, and "access_denied" means denied OR expired, so the
  local clock decides which one it was.
The approver is the Auth0 user who answers on the phone; it is not the user whose role is revoked.
Secrets and tokens are never logged, stored or put in error messages.
"""
from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Optional

from slothguard.auth.approvals import ApprovalStatus, RemediationAction

Transport = Callable[[str, dict], tuple]

MAX_PUSH_EXPIRY = 300
CIBA_GRANT = "urn:openid:params:grant-type:ciba"
_DISALLOWED = re.compile(r"[^A-Za-z0-9+\-_.,:#]")
REQUIRED_ENV = ("AUTH0_DOMAIN", "AUTH0_CLIENT_ID", "AUTH0_CLIENT_SECRET", "AUTH0_TEST_USER_ID")


class Auth0GatewayError(RuntimeError):
    """The approval service could not be used. Callers must treat it as "do not execute"."""


def make_binding_message(action: RemediationAction) -> str:
    """A short text shown on the phone, restricted to the characters Auth0 accepts."""
    raw = f"SoD#{action.rule_id}:revoke-{action.role}-from-{action.user_id}"
    return _DISALLOWED.sub("-", raw)[:64]


def _post_form(url: str, fields: dict) -> tuple:
    body = urllib.parse.urlencode(fields).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        try:
            return error.code, json.loads(raw)
        except json.JSONDecodeError:
            return error.code, {"error": "non_json_response"}
    except urllib.error.URLError as error:
        raise Auth0GatewayError(f"could not reach Auth0: {error.reason}") from error


@dataclass
class _Request:
    expires_at: float
    interval: float
    next_poll_at: float
    status: Optional[ApprovalStatus] = None


class Auth0CibaGateway:
    def __init__(
        self,
        domain: str,
        client_id: str,
        client_secret: str,
        approver_user_id: str,
        requested_expiry: int = 120,
        post: Optional[Transport] = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if not 1 <= requested_expiry <= MAX_PUSH_EXPIRY:
            raise ValueError(f"requested_expiry must be between 1 and {MAX_PUSH_EXPIRY} seconds")
        self.domain = domain.replace("https://", "").strip("/")
        self.requested_expiry = requested_expiry
        self._client_id = client_id
        self._client_secret = client_secret
        self._approver = approver_user_id
        self._post = post or _post_form
        self._clock = clock
        self._requests: dict[str, _Request] = {}

    def __repr__(self) -> str:
        return f"Auth0CibaGateway(domain={self.domain!r})"

    @classmethod
    def from_env(
        cls, env: Mapping[str, str], post: Optional[Transport] = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> "Auth0CibaGateway":
        missing = [name for name in REQUIRED_ENV if not env.get(name)]
        if missing:
            raise ValueError("Missing settings: " + ", ".join(missing))
        return cls(
            domain=env["AUTH0_DOMAIN"],
            client_id=env["AUTH0_CLIENT_ID"],
            client_secret=env["AUTH0_CLIENT_SECRET"],
            approver_user_id=env["AUTH0_TEST_USER_ID"],
            post=post,
            clock=clock,
        )

    def _call(self, path: str, fields: dict) -> tuple:
        try:
            return self._post(f"https://{self.domain}{path}", fields)
        except Auth0GatewayError:
            raise
        except Exception as error:
            # Only the exception type is reported: fields hold the client secret.
            raise Auth0GatewayError(f"request to Auth0 failed ({type(error).__name__})") from None

    def request_approval(self, action: RemediationAction) -> str:
        status, data = self._call("/bc-authorize", {
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "login_hint": json.dumps(
                {"format": "iss_sub", "iss": f"https://{self.domain}/", "sub": self._approver}
            ),
            "scope": "openid",
            "binding_message": make_binding_message(action),
            "requested_expiry": str(self.requested_expiry),
        })
        if status != 200 or not isinstance(data, dict) or "auth_req_id" not in data:
            detail = data.get("error") if isinstance(data, dict) else None
            raise Auth0GatewayError(f"bc-authorize failed (HTTP {status}): {detail}")
        now = self._clock()
        interval = float(data.get("interval", 5))
        request_id = str(data["auth_req_id"])
        self._requests[request_id] = _Request(
            expires_at=now + float(data.get("expires_in", self.requested_expiry)),
            interval=interval,
            next_poll_at=now + interval,
        )
        return request_id

    def get_status(self, request_id: str) -> ApprovalStatus:
        record = self._requests.get(request_id)
        if record is None:
            raise Auth0GatewayError("unknown approval request")
        if record.status is not None:
            return record.status

        now = self._clock()
        if now >= record.expires_at:
            record.status = ApprovalStatus.EXPIRED
            return record.status
        if now < record.next_poll_at:
            return ApprovalStatus.PENDING

        status, data = self._call("/oauth/token", {
            "grant_type": CIBA_GRANT,
            "client_id": self._client_id,
            "client_secret": self._client_secret,
            "auth_req_id": request_id,
        })
        data = data if isinstance(data, dict) else {}
        record.next_poll_at = now + record.interval

        if status == 200 and "access_token" in data:
            record.status = ApprovalStatus.APPROVED  # the token itself is dropped
            return record.status
        error = data.get("error")
        if error == "authorization_pending":
            return ApprovalStatus.PENDING
        if error == "slow_down":
            record.interval = max(record.interval, float(data.get("interval", record.interval + 5)))
            record.next_poll_at = now + record.interval
            return ApprovalStatus.PENDING
        if error == "access_denied":
            record.status = ApprovalStatus.DENIED
            return record.status
        raise Auth0GatewayError(f"unexpected answer from Auth0 (HTTP {status}): {error}")
