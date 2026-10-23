"""Manual check of Auth0CibaGateway together with RemediationExecutor. Nothing is really revoked.

Run it from the repository root (use the Python of the project virtual environment):
    python scripts/ciba_gateway_live.py
It sends one push approval request to the Auth0 test user (settings from .env), waits for the
answer on the phone and prints the result and the audit trail. No secret or token is printed.
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from slothguard.auth.approvals import RemediationAction, RemediationExecutor  # noqa: E402
from slothguard.auth.ciba import Auth0CibaGateway, Auth0GatewayError, make_binding_message  # noqa: E402
from slothguard.config import merged_env  # noqa: E402

EXIT_CODES = {"executed": 0, "denied": 3, "expired": 4, "error": 5, "waiting": 6}


class SimulatedRevoker:
    def __init__(self):
        self.calls = []

    def revoke(self, user_id, role):
        self.calls.append((user_id, role))
        print("SIMULATED revoke: %s from %s (nothing was changed anywhere)" % (role, user_id))


def main():
    try:
        gateway = Auth0CibaGateway.from_env(merged_env(ROOT / ".env"))
    except ValueError as error:
        print(error)
        return 1

    revoker = SimulatedRevoker()
    executor = RemediationExecutor(gateway, revoker)
    action = RemediationAction(kind="revoke_role", user_id="U001", role="Payment_Release", rule_id="SOD-001")
    try:
        pending = executor.propose(action)
    except Auth0GatewayError as error:
        print("Approval request FAILED: %s" % error)
        return 2

    print("Approval requested. Binding message: " + make_binding_message(action))
    print("Check the phone (Auth0 Guardian) and approve or deny.")
    started = time.time()
    deadline = started + gateway.requested_expiry + 10
    result = executor.execute(pending)
    while result == "waiting" and time.time() < deadline:
        time.sleep(2)
        result = executor.execute(pending)

    print("Result: %s after %.1f s" % (result, time.time() - started))
    print("Audit trail: " + ", ".join(entry.event for entry in executor.audit))
    print("Revocations made: %d (simulated)" % len(revoker.calls))
    return EXIT_CODES.get(result, 5)


if __name__ == "__main__":
    sys.exit(main())
