"""A fallback explanation says why it was used, so a failing model is never silent."""
from slothguard.llm import ExplanationCache, explain_finding
from slothguard.models import Finding


class FakeClient:
    def __init__(self, response):
        self.response = response

    def generate(self, prompt):
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def _finding(rules):
    rule = rules[0]
    return rule, Finding(rule_id=rule.id, user_id="U001", roles=rule.conflicting_roles, severity=rule.severity)


def test_a_client_error_gives_the_model_error_reason(rules):
    rule, finding = _finding(rules)
    result = explain_finding(finding, rule, FakeClient(RuntimeError("offline")))
    assert (result.source, result.reason) == ("fallback", "model_error")


def test_an_empty_answer_gives_the_empty_answer_reason(rules):
    rule, finding = _finding(rules)
    result = explain_finding(finding, rule, FakeClient("   "))
    assert (result.source, result.reason) == ("fallback", "empty_answer")


def test_too_many_sentences_gives_the_too_many_sentences_reason(rules):
    rule, finding = _finding(rules)
    result = explain_finding(finding, rule, FakeClient("One. Two. Three. Four. Five."))
    assert (result.source, result.reason) == ("fallback", "too_many_sentences")


def test_model_and_cache_answers_have_no_reason(rules):
    rule, finding = _finding(rules)
    cache = ExplanationCache()
    first = explain_finding(finding, rule, FakeClient("Good."), cache=cache)
    second = explain_finding(finding, rule, FakeClient("Not used."), cache=cache)
    assert (first.source, first.reason) == ("model", "")
    assert (second.source, second.reason) == ("cache", "")
