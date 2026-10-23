"""Reading settings from .env and the environment (names only, never printed)."""
from slothguard.config import load_env, merged_env


def test_load_env_parses_keys_values_quotes_comments_and_blank_lines(tmp_path):
    path = tmp_path / ".env"
    path.write_text('A=1\n# a comment\n\nB = "two"\nC=\'3\'\nD=with=equals\nnot a setting\n', encoding="utf-8")
    assert load_env(path) == {"A": "1", "B": "two", "C": "3", "D": "with=equals"}


def test_load_env_returns_an_empty_dict_when_the_file_is_missing(tmp_path):
    assert load_env(tmp_path / "missing.env") == {}


def test_merged_env_lets_the_environment_override_the_file_for_known_prefixes(tmp_path):
    path = tmp_path / ".env"
    path.write_text("AUTH0_DOMAIN=from-file\nOLLAMA_MODEL=file-model\n", encoding="utf-8")
    merged = merged_env(path, environ={"AUTH0_DOMAIN": "from-env", "PATH": "ignored", "OLLAMA_HOST": "http://h"})
    assert merged["AUTH0_DOMAIN"] == "from-env"
    assert merged["OLLAMA_MODEL"] == "file-model"
    assert merged["OLLAMA_HOST"] == "http://h"
    assert "PATH" not in merged


def test_merged_env_ignores_empty_environment_values(tmp_path):
    path = tmp_path / ".env"
    path.write_text("AUTH0_DOMAIN=from-file\n", encoding="utf-8")
    assert merged_env(path, environ={"AUTH0_DOMAIN": ""})["AUTH0_DOMAIN"] == "from-file"
