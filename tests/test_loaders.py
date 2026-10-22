"""Loading and validating the JSON exports (users and rules)."""
import json

import pytest

from slothguard.rules import load_rules, load_users


def _write(tmp_path, name, payload):
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _rule(**overrides):
    base = {"id": "R1", "name": "A vs B", "conflicting_roles": ["A", "B"],
            "severity": "high", "description": "d"}
    base.update(overrides)
    return base


def _user(**overrides):
    base = {"user_id": "U1", "name": "User 1", "unit": "Finance", "roles": ["A", "B"]}
    base.update(overrides)
    return base


def test_load_rules_returns_typed_rules(tmp_path):
    rules = load_rules(_write(tmp_path, "rules.json", [_rule()]))
    assert len(rules) == 1
    assert rules[0].id == "R1"
    assert rules[0].conflicting_roles == ("A", "B")
    assert rules[0].severity == "high"


def test_load_users_returns_typed_users(tmp_path):
    users = load_users(_write(tmp_path, "users.json", [_user()]))
    assert len(users) == 1
    assert users[0].user_id == "U1"
    assert users[0].roles == frozenset({"A", "B"})


def test_missing_file_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_rules(tmp_path / "nope.json")


@pytest.mark.parametrize("roles", [["A"], ["A", "B", "C"], [], ["A", "A"]])
def test_rule_must_have_two_distinct_roles(tmp_path, roles):
    path = _write(tmp_path, "rules.json", [_rule(conflicting_roles=roles)])
    with pytest.raises(ValueError):
        load_rules(path)


def test_rule_with_unknown_severity_is_rejected(tmp_path):
    path = _write(tmp_path, "rules.json", [_rule(severity="critical")])
    with pytest.raises(ValueError):
        load_rules(path)


def test_duplicate_rule_ids_are_rejected(tmp_path):
    path = _write(tmp_path, "rules.json", [_rule(), _rule(name="other")])
    with pytest.raises(ValueError):
        load_rules(path)


def test_rule_missing_id_is_rejected(tmp_path):
    bad = _rule()
    del bad["id"]
    with pytest.raises(ValueError):
        load_rules(_write(tmp_path, "rules.json", [bad]))


def test_user_missing_user_id_is_rejected(tmp_path):
    bad = _user()
    del bad["user_id"]
    with pytest.raises(ValueError):
        load_users(_write(tmp_path, "users.json", [bad]))


def test_duplicate_user_ids_are_rejected(tmp_path):
    path = _write(tmp_path, "users.json", [_user(), _user(name="other")])
    with pytest.raises(ValueError):
        load_users(path)


def test_user_roles_must_be_a_list(tmp_path):
    path = _write(tmp_path, "users.json", [_user(roles="A,B")])
    with pytest.raises(ValueError):
        load_users(path)
