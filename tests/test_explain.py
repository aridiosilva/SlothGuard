"""The model only explains findings. It never decides them and never blocks the report."""
from slothguard.llm import ExplanationCache, explain_finding
from slothguard.models import Finding


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.prompts = []

    def generate(self, prompt):
        self.prompts.append(prompt)
        response = self.responses.pop(0) if len(self.responses) > 1 else self.responses[0]
        if isinstance(response, Exception):
            raise response
        return response


def _finding(rules):
    rule = rules[0]
    return rule, Finding(rule_id=rule.id, user_id="U001",
                         roles=rule.conflicting_roles, severity=rule.severity)


def test_prompt_carries_the_facts_and_a_length_limit(rules):
    rule, finding = _finding(rules)
    client = FakeClient(["ok"])
    explain_finding(finding, rule, client)
    prompt = client.prompts[0]
    assert rule.name in prompt
    assert "U001" in prompt
    assert "Vendor_Maintain" in prompt and "Payment_Release" in prompt
    assert "high" in prompt.lower()
    assert "4 sentences" in prompt


def test_model_text_is_returned_stripped(rules):
    rule, finding = _finding(rules)
    result = explain_finding(finding, rule, FakeClient(["  Two roles conflict here.\n"]))
    assert result.text == "Two roles conflict here."
    assert result.source == "model"


def test_empty_model_output_falls_back_to_a_template(rules):
    rule, finding = _finding(rules)
    result = explain_finding(finding, rule, FakeClient(["   "]))
    assert result.source == "fallback"
    assert rule.name in result.text
    assert "U001" in result.text


def test_client_error_falls_back_and_does_not_raise(rules):
    rule, finding = _finding(rules)
    result = explain_finding(finding, rule, FakeClient([RuntimeError("model offline")]))
    assert result.source == "fallback"
    assert result.text.strip()


def test_fallback_text_is_deterministic(rules):
    rule, finding = _finding(rules)
    first = explain_finding(finding, rule, FakeClient([RuntimeError("x")]))
    second = explain_finding(finding, rule, FakeClient([RuntimeError("y")]))
    assert first.text == second.text


def test_cache_hit_skips_the_model(rules):
    rule, finding = _finding(rules)
    cache = ExplanationCache()
    client = FakeClient(["Cached explanation."])
    first = explain_finding(finding, rule, client, cache=cache)
    second = explain_finding(finding, rule, client, cache=cache)
    assert first.source == "model"
    assert second.source == "cache"
    assert second.text == "Cached explanation."
    assert len(client.prompts) == 1


def test_fallback_is_not_cached_so_a_later_call_can_recover(rules):
    rule, finding = _finding(rules)
    cache = ExplanationCache()
    client = FakeClient([RuntimeError("temporary"), "Recovered explanation."])
    first = explain_finding(finding, rule, client, cache=cache)
    second = explain_finding(finding, rule, client, cache=cache)
    assert first.source == "fallback"
    assert second.source == "model"
    assert second.text == "Recovered explanation."
