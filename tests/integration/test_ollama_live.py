"""Needs a local Ollama server. Skipped unless RUN_OLLAMA_TESTS=1.

Run with:  $env:RUN_OLLAMA_TESTS = "1"; python -m pytest tests/integration -s
The -s flag lets you see the elapsed time, which is raw material for the post.
"""
import os
import time

import pytest

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.environ.get("RUN_OLLAMA_TESTS") != "1",
                       reason="set RUN_OLLAMA_TESTS=1 to run against a local Ollama server"),
]


def test_ollama_returns_a_short_answer():
    from slothguard.llm import OllamaClient

    client = OllamaClient(host=os.environ.get("OLLAMA_HOST", "http://localhost:11434"),
                          model=os.environ.get("OLLAMA_MODEL", "gemma4:e2b"))
    start = time.perf_counter()
    answer = client.generate("Reply with one short sentence about segregation of duties.")
    elapsed = time.perf_counter() - start
    print(f"\nollama answered in {elapsed:.1f}s: {answer!r}")
    assert isinstance(answer, str) and answer.strip()
