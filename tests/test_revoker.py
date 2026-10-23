"""In-memory role revoker: the simulated side effect of an approved revocation."""
import pytest

from slothguard.revoker import InMemoryRoleRevoker
from slothguard.rules import detect_conflicts


def test_revoking_removes_only_that_role(make_user):
    revoker = InMemoryRoleRevoker([make_user("U1", ["Vendor_Maintain", "Payment_Release", "Report_Viewer"])])
    revoker.revoke("U1", "Payment_Release")
    assert revoker.users()[0].roles == frozenset({"Vendor_Maintain", "Report_Viewer"})


def test_the_original_users_are_not_mutated(make_user):
    original = make_user("U1", ["Vendor_Maintain", "Payment_Release"])
    InMemoryRoleRevoker([original]).revoke("U1", "Payment_Release")
    assert original.roles == frozenset({"Vendor_Maintain", "Payment_Release"})


def test_role_matching_ignores_case_and_spaces_like_the_rule_engine(make_user):
    revoker = InMemoryRoleRevoker([make_user("U1", ["Vendor_Maintain", "payment_release"])])
    revoker.revoke("U1", " Payment_Release ")
    assert revoker.users()[0].roles == frozenset({"Vendor_Maintain"})


def test_unknown_user_is_an_error(make_user):
    with pytest.raises(ValueError):
        InMemoryRoleRevoker([make_user("U1", ["A"])]).revoke("U9", "A")


def test_a_role_the_user_does_not_hold_is_an_error(make_user):
    with pytest.raises(ValueError):
        InMemoryRoleRevoker([make_user("U1", ["A"])]).revoke("U1", "B")


def test_revoking_one_role_clears_the_finding(rules, make_user):
    revoker = InMemoryRoleRevoker([make_user("U1", ["Vendor_Maintain", "Payment_Release"])])
    assert len(detect_conflicts(revoker.users(), rules)) == 1
    revoker.revoke("U1", "Payment_Release")
    assert detect_conflicts(revoker.users(), rules) == []
