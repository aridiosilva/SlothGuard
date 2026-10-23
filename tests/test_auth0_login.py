"""The Authlib wrapper: only the parts that need no network."""
from urllib.parse import parse_qs, urlparse

from flask import Flask

from slothguard.web.auth0_login import Auth0Login


def test_logout_url_points_to_auth0_with_the_return_address_and_client_id():
    login = Auth0Login("https://dev-test.us.auth0.com/", "cid", "the-secret")
    parts = urlparse(login.logout_url("http://localhost:8000/"))
    assert (parts.scheme, parts.netloc, parts.path) == ("https", "dev-test.us.auth0.com", "/v2/logout")
    assert parse_qs(parts.query) == {"returnTo": ["http://localhost:8000/"], "client_id": ["cid"]}


def test_the_secret_is_not_in_the_repr():
    assert "the-secret" not in repr(Auth0Login("dev-test.us.auth0.com", "cid", "the-secret"))


def test_init_app_registers_the_client_without_touching_the_network():
    app = Flask(__name__)
    app.secret_key = "test"
    login = Auth0Login("dev-test.us.auth0.com", "cid", "the-secret")
    login.init_app(app)
    assert login._client is not None
