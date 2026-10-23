"""The explanation cache can be saved to and loaded from a JSON file (model answers only)."""
import json

import pytest

from slothguard.llm import ExplanationCache
from slothguard.models import Finding


def _finding(rule_id="R1", user_id="U1"):
    return Finding(rule_id=rule_id, user_id=user_id, roles=("A", "B"), severity="high")


def test_a_saved_cache_can_be_loaded_back(tmp_path):
    cache = ExplanationCache()
    cache.put(_finding("R1", "U1"), "First explanation.")
    cache.put(_finding("R2", "U2"), "Second explanation.")
    path = tmp_path / "out" / "explanations.json"
    cache.save(path)
    loaded = ExplanationCache.load(path)
    assert loaded.get(_finding("R1", "U1")) == "First explanation."
    assert loaded.get(_finding("R2", "U2")) == "Second explanation."
    assert loaded.get(_finding("R3", "U3")) is None


def test_loading_a_missing_file_gives_an_empty_cache(tmp_path):
    assert ExplanationCache.load(tmp_path / "missing.json").get(_finding()) is None


def test_the_file_holds_only_ids_and_text(tmp_path):
    cache = ExplanationCache()
    cache.put(_finding(), "Some text.")
    path = tmp_path / "cache.json"
    cache.save(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["entries"] == [{"rule_id": "R1", "user_id": "U1", "text": "Some text."}]


@pytest.mark.parametrize("content", ["not json", "[]", '{"entries": "nope"}', '{"entries": [{"rule_id": "R1"}]}'])
def test_a_malformed_file_is_an_error(tmp_path, content):
    path = tmp_path / "bad.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ValueError):
        ExplanationCache.load(path)
