"""Contract for the deterministic SoD engine: the rules detect, the model never does."""
import random

from slothguard.rules import detect_conflicts


def test_no_users_means_no_findings(rules):
    assert detect_conflicts([], rules) == []


def test_no_rules_means_no_findings(make_user):
    assert detect_conflicts([make_user("U1", ["Vendor_Maintain", "Payment_Release"])], []) == []


def test_user_holding_both_roles_triggers_a_finding(rules, make_user):
    findings = detect_conflicts([make_user("U1", ["Vendor_Maintain", "Payment_Release"])], rules)
    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == "R1"
    assert f.user_id == "U1"
    assert f.severity == "high"
    assert f.roles == ("Vendor_Maintain", "Payment_Release")


def test_user_holding_only_one_role_is_clean(rules, make_user):
    assert detect_conflicts([make_user("U1", ["Vendor_Maintain"])], rules) == []
    assert detect_conflicts([make_user("U2", ["Payment_Release"])], rules) == []


def test_unrelated_roles_are_ignored(rules, make_user):
    assert detect_conflicts([make_user("U1", ["Report_Viewer", "Helpdesk"])], rules) == []


def test_role_matching_ignores_case_and_surrounding_spaces(rules, make_user):
    user = make_user("U1", ["vendor_maintain", "  PAYMENT_RELEASE "])
    findings = detect_conflicts([user], rules)
    assert [f.rule_id for f in findings] == ["R1"]


def test_one_finding_per_user_and_rule_even_with_extra_roles(rules, make_user):
    user = make_user("U1", ["Vendor_Maintain", "Payment_Release", "Report_Viewer"])
    findings = detect_conflicts([user], rules)
    assert len(findings) == 1


def test_user_can_trigger_several_rules(rules, make_user):
    user = make_user("U1", ["Vendor_Maintain", "Payment_Release", "Requester", "Approver"])
    findings = detect_conflicts([user], rules)
    assert sorted(f.rule_id for f in findings) == ["R1", "R2"]


def test_each_user_is_evaluated_independently(rules, make_user):
    users = [
        make_user("U1", ["Vendor_Maintain", "Payment_Release"]),
        make_user("U2", ["Vendor_Maintain"]),
        make_user("U3", ["Payment_Release"]),
    ]
    findings = detect_conflicts(users, rules)
    assert [f.user_id for f in findings] == ["U1"]


def test_findings_sorted_by_severity_then_user_then_rule(rules, make_user):
    users = [
        make_user("U2", ["Adjust", "Count_Approve"]),                      # low
        make_user("U3", ["Requester", "Approver"]),                        # medium
        make_user("U1", ["Vendor_Maintain", "Payment_Release"]),           # high
        make_user("U0", ["Requester", "Approver"]),                        # medium
    ]
    findings = detect_conflicts(users, rules)
    assert [(f.severity, f.user_id, f.rule_id) for f in findings] == [
        ("high", "U1", "R1"),
        ("medium", "U0", "R2"),
        ("medium", "U3", "R2"),
        ("low", "U2", "R3"),
    ]


def test_result_does_not_depend_on_input_order(rules, make_user):
    users = [
        make_user("U1", ["Vendor_Maintain", "Payment_Release"]),
        make_user("U2", ["Requester", "Approver"]),
        make_user("U3", ["Adjust", "Count_Approve"]),
        make_user("U4", ["Vendor_Maintain", "Payment_Release", "Requester", "Approver"]),
    ]
    baseline = detect_conflicts(users, rules)
    rng = random.Random(7)
    for _ in range(10):
        shuffled_users, shuffled_rules = users[:], rules[:]
        rng.shuffle(shuffled_users)
        rng.shuffle(shuffled_rules)
        assert detect_conflicts(shuffled_users, shuffled_rules) == baseline


def test_inputs_are_not_mutated(rules, make_user):
    users = [make_user("U1", ["Vendor_Maintain", "Payment_Release"])]
    users_before, rules_before = list(users), list(rules)
    detect_conflicts(users, rules)
    assert users == users_before
    assert rules == rules_before
