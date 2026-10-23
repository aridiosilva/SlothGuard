"""Run the SlothGuard web interface on this computer only.

Run it from the repository root (use the Python of the project virtual environment):
    python scripts/run_app.py
Then open http://localhost:8000 in the browser. The address must be exactly localhost:8000,
because that is what is registered in the Auth0 application (callback and logout URLs).

Settings come from .env (AUTH0_DOMAIN, AUTH0_CLIENT_ID, AUTH0_CLIENT_SECRET, AUTH0_TEST_USER_ID).
The Auth0 user in AUTH0_TEST_USER_ID is the person who approves revocations on their phone.
No secret is printed.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from slothguard.auth.ciba import Auth0CibaGateway  # noqa: E402
from slothguard.config import merged_env  # noqa: E402
from slothguard.llm import ExplanationCache  # noqa: E402
from slothguard.rules import load_rules, load_users  # noqa: E402
from slothguard.web import create_app  # noqa: E402
from slothguard.web.auth0_login import Auth0Login  # noqa: E402

HOST = "127.0.0.1"
PORT = 8000
BASE_URL = "http://localhost:%d" % PORT


def main():
    env = merged_env(ROOT / ".env")
    try:
        gateway = Auth0CibaGateway.from_env(env)
    except ValueError as error:
        print(error)
        return 1

    users = load_users(ROOT / "data" / "synthetic" / "users.json")
    rules = load_rules(ROOT / "data" / "synthetic" / "sod_rules.json")
    cache = ExplanationCache.load(ROOT / "data" / "output" / "explanations.json")
    auth = Auth0Login(env["AUTH0_DOMAIN"], env["AUTH0_CLIENT_ID"], env["AUTH0_CLIENT_SECRET"])
    app = create_app(users=users, rules=rules, gateway=gateway, auth=auth, cache=cache, base_url=BASE_URL)

    print("SlothGuard is running. Open %s in the browser (not 127.0.0.1)." % BASE_URL)
    print("Press Ctrl+C to stop.")
    app.run(host=HOST, port=PORT, debug=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
