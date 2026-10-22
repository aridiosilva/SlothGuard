import pytest

from slothguard.models import SoDRule, UserAccess


@pytest.fixture
def rules():
    return [
        SoDRule(id="R1", name="Vendor maintenance vs. payment release",
                conflicting_roles=("Vendor_Maintain", "Payment_Release"),
                severity="high", description="Could create and pay a fictitious vendor."),
        SoDRule(id="R2", name="Request vs. approval",
                conflicting_roles=("Requester", "Approver"),
                severity="medium", description="Could approve their own request."),
        SoDRule(id="R3", name="Adjustment vs. count approval",
                conflicting_roles=("Adjust", "Count_Approve"),
                severity="low", description="Could adjust stock and approve the count."),
    ]


@pytest.fixture
def make_user():
    def _make(user_id, roles, unit="Finance"):
        return UserAccess(user_id=user_id, name=f"User {user_id}", unit=unit,
                          roles=frozenset(roles))
    return _make
