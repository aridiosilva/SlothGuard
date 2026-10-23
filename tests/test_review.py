"""End-to-end review logic (no network): detect, explain each finding once, build the report."""
from datetime import date

from slothguard.llm import ExplanationCache
from slothguard.review import run_review

TODAY = date(2026, 10, 23)


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


def _two_conflicts(make_user):
    return [
        make_user("U1", ["Vendor_Maintain", "Payment_Release"]),   # high
        make_user("U2", ["Requester", "Approver"]),                # medium
        make_user("U3", ["Report_Viewer"]),                        # clean
    ]


def test_no_conflicts_gives_an_empty_report_and_never_calls_the_model(rules, make_user):
    client = FakeClient(["unused"])
    result = run_review([make_user("U1", ["Report_Viewer"])], rules, client, TODAY)
    assert result.findings == []
    assert "No SoD conflicts found" in result.report
    assert client.prompts == []
    assert result.counts == {"model": 0, "cache": 0, "fallback": 0}


def test_each_finding_is_explained_exactly_once(rules, make_user):
    client = FakeClient(["Good explanation."])
    result = run_review(_two_conflicts(make_user), rules, client, TODAY)
    assert len(result.findings) == 2
    assert len(client.prompts) == 2
    assert set(result.explanations) == {("R1", "U1"), ("R2", "U2")}


def test_explanations_appear_in_the_report_in_finding_order(rules, make_user):
    client = FakeClient(["Good explanation."])
    result = run_review(_two_conflicts(make_user), rules, client, TODAY)
    assert result.report.count("Good explanation.") == 2
    assert result.report.index("### R1 | U1") < result.report.index("### R2 | U2")
    assert "2026-10-23" in result.report


def test_counts_separate_model_answers_from_fallbacks(rules, make_user):
    client = FakeClient(["Good explanation.", RuntimeError("model offline")])
    result = run_review(_two_conflicts(make_user), rules, client, TODAY)
    assert result.counts == {"model": 1, "cache": 0, "fallback": 1}


def test_a_failing_model_still_gives_a_complete_report(rules, make_user):
    client = FakeClient([RuntimeError("model offline")])
    result = run_review(_two_conflicts(make_user), rules, client, TODAY)
    assert result.counts["fallback"] == 2
    assert result.report.count("Source: fallback") == 2
    assert "### R1 | U1" in result.report and "### R2 | U2" in result.report


def test_a_second_run_with_the_same_cache_does_not_call_the_model(rules, make_user):
    cache = ExplanationCache()
    users = _two_conflicts(make_user)
    first_client = FakeClient(["Good explanation."])
    run_review(users, rules, first_client, TODAY, cache=cache)
    second_client = FakeClient(["Should not be used."])
    result = run_review(users, rules, second_client, TODAY, cache=cache)
    assert second_client.prompts == []
    assert result.counts == {"model": 0, "cache": 2, "fallback": 0}


def test_progress_callback_is_called_once_per_finding(rules, make_user):
    seen = []
    client = FakeClient(["Good explanation."])
    run_review(_two_conflicts(make_user), rules, client, TODAY,
               on_progress=lambda index, total, finding, explanation: seen.append(
                   (index, total, finding.rule_id, explanation.source)))
    assert seen == [(1, 2, "R1", "model"), (2, 2, "R2", "model")]


def test_the_report_is_the_same_for_the_same_inputs(rules, make_user):
    users = _two_conflicts(make_user)
    first = run_review(users, rules, FakeClient(["Good explanation."]), TODAY)
    second = run_review(users, rules, FakeClient(["Good explanation."]), TODAY)
    assert first.report == second.report
