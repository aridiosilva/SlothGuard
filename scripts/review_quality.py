"""Quality check of the saved explanations. No model is called.

For each finding it shows how many sentences the explanation has and which severity words it uses
(critical, high, medium, low, severe), and flags words that are not the severity given by the rule.
Run it from the repository root (use the Python of the project virtual environment):
    python scripts/review_quality.py
    python scripts/review_quality.py --out docs/evidence/review-quality.md
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from slothguard.llm import MAX_SENTENCES, ExplanationCache, count_sentences  # noqa: E402
from slothguard.rules import detect_conflicts, load_rules, load_users  # noqa: E402

SEVERITY_WORDS = ("critical", "severe", "high", "medium", "low")


def main():
    parser = argparse.ArgumentParser(description="Check the saved explanations.")
    parser.add_argument("--cache", default=str(ROOT / "data" / "output" / "explanations.json"))
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    cache = ExplanationCache.load(args.cache)
    users = load_users(ROOT / "data" / "synthetic" / "users.json")
    rules = load_rules(ROOT / "data" / "synthetic" / "sod_rules.json")
    findings = detect_conflicts(users, rules)

    lines = [
        "# Explanation quality check",
        "",
        "| Finding | Rule severity | Sentences | Severity words used | Differs from the rule |",
        "|---|---|---|---|---|",
    ]
    explained = within_limit = with_mismatch = 0
    for finding in findings:
        text = cache.get(finding)
        label = "%s / %s" % (finding.rule_id, finding.user_id)
        if text is None:
            lines.append("| %s | %s | not generated | | |" % (label, finding.severity))
            continue
        explained += 1
        sentences = count_sentences(text)
        words = [w for w in SEVERITY_WORDS if re.search(r"\b%s\b" % w, text, re.IGNORECASE)]
        differs = [w for w in words if w != finding.severity]
        within_limit += sentences <= MAX_SENTENCES
        with_mismatch += bool(differs)
        lines.append("| %s | %s | %d | %s | %s |" % (
            label, finding.severity, sentences, ", ".join(words) or "-", ", ".join(differs) or "-"))
    lines += [
        "",
        "Findings: %d | explained: %d | within %d sentences: %d | using a severity word different from the rule: %d" % (
            len(findings), explained, MAX_SENTENCES, within_limit, with_mismatch),
    ]
    text = "\n".join(lines) + "\n"
    print(text)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text, encoding="utf-8", newline="\n")
        print("Saved to: " + args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
