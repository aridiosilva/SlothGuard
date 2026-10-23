"""Run a full SoD review with the local Ollama model, then save the report, the explanations
and a run log.

Run it from the repository root, with Ollama running and nothing heavy open
(use the Python of the project virtual environment):
    python scripts/run_review.py --conditions "free RAM 6.1 GB; best performance"

Reads OLLAMA_HOST and OLLAMA_MODEL from the environment or from .env. Prints no secrets.
It stops at once, before doing any work, if Ollama cannot be reached.
"""
import argparse
import socket
import sys
import time
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from slothguard.config import merged_env  # noqa: E402
from slothguard.llm import ExplanationCache, OllamaClient  # noqa: E402
from slothguard.review import run_review  # noqa: E402
from slothguard.rules import load_rules, load_users  # noqa: E402


def write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def ollama_reachable(host):
    parts = urlparse(host)
    try:
        with socket.create_connection((parts.hostname or "localhost", parts.port or 11434), timeout=3):
            return True
    except OSError:
        return False


def main():
    parser = argparse.ArgumentParser(description="Run a full SoD review with the local model.")
    parser.add_argument("--users", default=str(ROOT / "data" / "synthetic" / "users.json"))
    parser.add_argument("--rules", default=str(ROOT / "data" / "synthetic" / "sod_rules.json"))
    parser.add_argument("--out", default=str(ROOT / "docs" / "evidence" / "report-sample.md"))
    parser.add_argument("--log", default=str(ROOT / "docs" / "evidence" / "review-run.md"))
    parser.add_argument("--cache-out", default=str(ROOT / "data" / "output" / "explanations.json"))
    parser.add_argument("--think", action="store_true", help="let the model think (slower)")
    parser.add_argument("--conditions", default="not recorded",
                        help="free text: free RAM, power mode, programs open")
    args = parser.parse_args()

    env = merged_env(ROOT / ".env")
    host = env.get("OLLAMA_HOST") or "http://localhost:11434"
    model = env.get("OLLAMA_MODEL") or "gemma4:e2b"

    if not ollama_reachable(host):
        print("Ollama is not reachable at %s. Open the Ollama app (or run 'ollama serve'), wait "
              "a few seconds and try again. Nothing was done." % host)
        return 2

    users = load_users(args.users)
    rules = load_rules(args.rules)
    client = OllamaClient(host=host, model=model, think=True if args.think else False)
    cache = ExplanationCache()

    timings = []
    state = {"last": time.perf_counter()}

    def on_progress(index, total, finding, explanation):
        now = time.perf_counter()
        seconds = now - state["last"]
        state["last"] = now
        timings.append((finding, explanation, seconds))
        shown = explanation.source + (" [%s]" % explanation.reason if explanation.reason else "")
        print("[%d/%d] %s | %s -> %s (%.1f s)" % (
            index, total, finding.rule_id, finding.user_id, shown, seconds))

    print("Model: %s | thinking: %s | users: %d | rules: %d" % (
        model, "on" if args.think else "off", len(users), len(rules)))
    started = time.perf_counter()
    state["last"] = started
    result = run_review(users, rules, client, date.today(), cache=cache, on_progress=on_progress)
    total_seconds = time.perf_counter() - started

    write_text(args.out, result.report)
    cache.save(args.cache_out)
    lines = [
        "# Review run",
        "",
        "Date: %s" % date.today().isoformat(),
        "Model: %s (thinking %s)" % (model, "on" if args.think else "off"),
        "Users: %d | Rules: %d | Findings: %d" % (len(users), len(rules), len(result.findings)),
        "Explanations by source: model=%d, cache=%d, fallback=%d" % (
            result.counts["model"], result.counts["cache"], result.counts["fallback"]),
        "Total time: %.1f s" % total_seconds,
        "Conditions: %s" % args.conditions,
        "",
        "Per finding (the first one includes loading the model):",
    ]
    for finding, explanation, seconds in timings:
        reason = ", reason %s" % explanation.reason if explanation.reason else ""
        lines.append("- %s | %s: %s%s, %.1f s" % (
            finding.rule_id, finding.user_id, explanation.source, reason, seconds))
    write_text(args.log, "\n".join(lines) + "\n")

    print("Total time: %.1f s" % total_seconds)
    print("Report saved to: %s" % args.out)
    print("Run log saved to: %s" % args.log)
    print("Explanations saved to: %s" % args.cache_out)
    if result.findings and result.counts["model"] == 0:
        print("WARNING: every explanation used the fallback text. See the reasons above.")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
