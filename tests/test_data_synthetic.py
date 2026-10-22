"""Guards the constitution: only synthetic data in the repository."""
import json
from pathlib import Path

from slothguard.rules import detect_conflicts, load_rules, load_users

DATA = Path(__file__).resolve().parents[1] / "data" / "synthetic"


def test_every_user_record_is_flagged_synthetic():
    raw = json.loads((DATA / "users.json").read_text(encoding="utf-8"))
    assert raw, "users.json must not be empty"
    assert all(record.get("synthetic") is True for record in raw)


def test_dataset_has_the_agreed_minimum_size():
    assert len(load_users(DATA / "users.json")) >= 30
    assert len(load_rules(DATA / "sod_rules.json")) >= 8


def test_dataset_produces_findings_and_clean_users():
    users = load_users(DATA / "users.json")
    rules = load_rules(DATA / "sod_rules.json")
    findings = detect_conflicts(users, rules)
    assert len(findings) >= 5
    assert {"high"}.issubset({f.severity for f in findings})
    flagged = {f.user_id for f in findings}
    assert any(u.user_id not in flagged for u in users)
