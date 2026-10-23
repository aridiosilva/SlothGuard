"""Sign in with Auth0 (Universal Login, authorization code flow) using Authlib.

The login backend used by slothguard.web.create_app has three methods:
    login_redirect(redirect_uri) -> response that sends the browser to Auth0
    fetch_user()                 -> dict with the user's claims (on the callback request)
    logout_url(return_to)        -> address that signs the user out of Auth0
The client secret never leaves this object and is not in its repr.
"""
from __future__ import annotations

from urllib.parse import urlencode

from authlib.integrations.flask_client import OAuth

from slothguard.web.auth_base import LoginError


class Auth0Login:
    def __init__(self, domain: str, client_id: str, client_secret: str) -> None:
        self.domain = domain.replace("https://", "").strip("/")
        self.client_id = client_id
        self._client_secret = client_secret
        self._oauth = OAuth()
        self._client = None

    def __repr__(self) -> str:
        return f"Auth0Login(domain={self.domain!r})"

    def init_app(self, app) -> None:
        self._oauth.init_app(app)
        self._client = self._oauth.register(
            "auth0",
            client_id=self.client_id,
            client_secret=self._client_secret,
            client_kwargs={"scope": "openid profile email"},
            server_metadata_url=f"https://{self.domain}/.well-known/openid-configuration",
        )

    def login_redirect(self, redirect_uri: str):
        return self._client.authorize_redirect(redirect_uri=redirect_uri)

    def fetch_user(self) -> dict:
        try:
            token = self._client.authorize_access_token()
        except Exception as error:
            raise LoginError("Login failed. Please try again.") from error
        userinfo = token.get("userinfo") or {}
        if not userinfo.get("sub"):
            raise LoginError("Login failed: no user came back from Auth0.")
        return dict(userinfo)

    def logout_url(self, return_to: str) -> str:
        return f"https://{self.domain}/v2/logout?" + urlencode(
            {"returnTo": return_to, "client_id": self.client_id}
        )
