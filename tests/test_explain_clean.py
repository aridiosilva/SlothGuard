"""Model answers often carry Markdown decoration (escaped underscores, backticks, bold marks).
It is removed so the web page and the saved cache show plain text."""
import json

import pytest

from slothguard.llm import ExplanationCache, clean_model_text, explain_finding
from slothguard.models import Finding


class FakeClient:
    def __init__(self, response):
        self.response = response

    def generate(self, prompt):
        return self.response


@pytest.mark.parametrize("raw, expected", [
    (r"Holding both Vendor\_Master\_Maintain and Payment\_Release.", "Holding both Vendor_Master_Maintain and Payment_Release."),
    ("Holding both `Journal_Entry_Create` and `Journal_Entry_Approve`.", "Holding both Journal_Entry_Create and Journal_Entry_Approve."),
    ("This is **very** important.", "This is very important."),
    ("Plain text stays as it is.", "Plain text stays as it is."),
    (r"Escaped star \* and hash \# too.", "Escaped star * and hash # too."),
    ("  padded  ", "padded"),
])
def test_clean_model_text(raw, expected):
    assert clean_model_text(raw) == expected


def _finding(rules):
    rule = rules[0]
    return rule, Finding(rule_id=rule.id, user_id="U1", roles=rule.conflicting_roles, severity=rule.severity)


def test_explain_finding_returns_and_caches_the_cleaned_text(rules):
    rule, finding = _finding(rules)
    cache = ExplanationCache()
    result = explain_finding(finding, rule, FakeClient(r"Roles `Vendor\_Maintain` and **Payment\_Release** conflict."), cache=cache)
    assert result.text == "Roles Vendor_Maintain and Payment_Release conflict."
    assert cache.get(finding) == result.text


def test_an_answer_that_is_only_decoration_counts_as_empty(rules):
    rule, finding = _finding(rules)
    result = explain_finding(finding, rule, FakeClient("`` **"))
    assert (result.source, result.reason) == ("fallback", "empty_answer")


def test_loading_an_old_cache_file_cleans_its_text(tmp_path, rules):
    _, finding = _finding(rules)
    path = tmp_path / "cache.json"
    path.write_text(json.dumps({"version": 1, "entries": [
        {"rule_id": finding.rule_id, "user_id": "U1", "text": r"Both `Vendor\_Maintain` roles."}]}), encoding="utf-8")
    assert ExplanationCache.load(path).get(finding) == "Both Vendor_Maintain roles."
