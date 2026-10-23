"""Minimal CIBA smoke test (manual check, not a unit test).

Sends one push approval request to the Auth0 test user and waits for the answer.
Reads the credentials from .env (never printed). Uses only the standard library.
Run it from the repository root with the project Python: scripts/ciba_smoke_test.py
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

REQUIRED = ("AUTH0_DOMAIN", "AUTH0_CLIENT_ID", "AUTH0_CLIENT_SECRET", "AUTH0_TEST_USER_ID")


def load_env(path=".env"):
    values = {}
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def post_form(url, fields):
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
            return error.code, {"error": "non_json_response", "error_description": raw[:200]}
    except urllib.error.URLError as error:
        return 0, {"error": "network_error", "error_description": str(error.reason)}


def main():
    try:
        env = load_env()
    except FileNotFoundError:
        print("File .env not found. Run this from the repository root.")
        return 1
    missing = [key for key in REQUIRED if not env.get(key)]
    if missing:
        print("Missing values in .env: " + ", ".join(missing))
        return 1

    domain = env["AUTH0_DOMAIN"].replace("https://", "").strip("/")
    base = "https://" + domain
    binding = "SOD-TEST#" + str(int(time.time()) % 100000)
    login_hint = json.dumps(
        {"format": "iss_sub", "iss": base + "/", "sub": env["AUTH0_TEST_USER_ID"]}
    )

    started = time.time()
    status, data = post_form(base + "/bc-authorize", {
        "client_id": env["AUTH0_CLIENT_ID"],
        "client_secret": env["AUTH0_CLIENT_SECRET"],
        "login_hint": login_hint,
        "scope": "openid",
        "binding_message": binding,
        "requested_expiry": "120",
    })
    if status != 200 or "auth_req_id" not in data:
        print("bc-authorize FAILED (HTTP %s): %s - %s" % (
            status, data.get("error"), data.get("error_description")))
        return 2

    print("Request accepted. Binding message: " + binding)
    print("Check the phone (Auth0 Guardian) and approve or deny.")
    interval = int(data.get("interval", 5))
    deadline = started + int(data.get("expires_in", 120))

    while time.time() < deadline:
        time.sleep(interval)
        status, token = post_form(base + "/oauth/token", {
            "grant_type": "urn:openid:params:grant-type:ciba",
            "client_id": env["AUTH0_CLIENT_ID"],
            "client_secret": env["AUTH0_CLIENT_SECRET"],
            "auth_req_id": data["auth_req_id"],
        })
        elapsed = time.time() - started
        if status == 200 and "access_token" in token:
            print("APPROVED after %.1f s (token_type=%s, expires_in=%s; tokens not printed)" % (
                elapsed, token.get("token_type"), token.get("expires_in")))
            return 0
        error = token.get("error")
        if error == "authorization_pending":
            continue
        if error == "slow_down":
            interval = int(token.get("interval", interval + 5))
            continue
        if error == "access_denied":
            print("DENIED or expired after %.1f s" % elapsed)
            return 3
        print("Unexpected response (HTTP %s): %s - %s" % (
            status, error, token.get("error_description")))
        return 4

    print("Timed out waiting for the answer.")
    return 5


if __name__ == "__main__":
    sys.exit(main())
