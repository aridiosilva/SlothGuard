"""Report builder: pure function from findings and explanations to Markdown."""
from datetime import date

from slothguard.llm import Explanation
from slothguard.models import Finding
from slothguard.report import build_report

TODAY = date(2026, 10, 22)


def _f(rule_id, user_id, severity, roles=("A", "B")):
    return Finding(rule_id=rule_id, user_id=user_id, roles=roles, severity=severity)


def test_empty_report_says_no_conflicts_and_shows_the_date():
    report = build_report([], {}, TODAY)
    assert report.startswith("# SoD Review Report")
    assert "No SoD conflicts found" in report
    assert "2026-10-22" in report


def test_summary_counts_by_severity():
    findings = [_f("R1", "U1", "high"), _f("R1", "U2", "high"), _f("R2", "U3", "medium")]
    report = build_report(findings, {}, TODAY)
    assert "High: 2" in report
    assert "Medium: 1" in report
    assert "Low: 0" in report


def test_each_finding_has_exactly_one_heading():
    findings = [_f("R1", "U1", "high"), _f("R2", "U2", "medium")]
    report = build_report(findings, {}, TODAY)
    assert report.count("### R1 | U1") == 1
    assert report.count("### R2 | U2") == 1


def test_report_keeps_the_order_it_was_given():
    findings = [_f("R2", "U9", "medium"), _f("R1", "U1", "high")]
    report = build_report(findings, {}, TODAY)
    assert report.index("### R2 | U9") < report.index("### R1 | U1")


def test_finding_shows_severity_and_both_roles():
    report = build_report([_f("R1", "U1", "high", ("Vendor_Maintain", "Payment_Release"))], {}, TODAY)
    assert "Severity: High" in report
    assert "Vendor_Maintain" in report and "Payment_Release" in report


def test_explanation_text_and_source_are_included():
    findings = [_f("R1", "U1", "high")]
    explanations = {("R1", "U1"): Explanation(text="Both roles allow self-approval.", source="model")}
    report = build_report(findings, explanations, TODAY)
    assert "Both roles allow self-approval." in report
    assert "Source: model" in report


def test_fallback_explanations_are_labelled():
    findings = [_f("R1", "U1", "high")]
    explanations = {("R1", "U1"): Explanation(text="Template text.", source="fallback")}
    report = build_report(findings, explanations, TODAY)
    assert "Source: fallback" in report


def test_missing_explanation_is_stated_not_hidden():
    report = build_report([_f("R1", "U1", "high")], {}, TODAY)
    assert "Explanation not available" in report


def test_same_inputs_give_the_same_report():
    findings = [_f("R1", "U1", "high"), _f("R2", "U2", "low")]
    explanations = {("R1", "U1"): Explanation(text="x", source="model")}
    assert build_report(findings, explanations, TODAY) == build_report(findings, explanations, TODAY)
