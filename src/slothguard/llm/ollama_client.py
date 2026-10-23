"""Client for a local Ollama server (POST /api/generate).

Thinking is switched off by default: the measured gain on gemma4:e2b was about 81% fewer
generated tokens and about 4.3x less time per explanation. Any failure is reported as
OllamaError, so callers can fall back to a deterministic text.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable, Optional

Transport = Callable[[str, dict, float], dict]


class OllamaError(RuntimeError):
    """Raised when the Ollama server cannot be reached or answers something unusable."""


def _http_post(url: str, payload: dict, timeout: float) -> dict:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    # An empty ProxyHandler keeps local calls from going through a system proxy.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as error:
        raise OllamaError(f"Ollama answered HTTP {error.code}") from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise OllamaError(f"Could not reach Ollama: {error}") from error
    try:
        data: Any = json.loads(raw)
    except json.JSONDecodeError as error:
        raise OllamaError("Ollama answered something that is not JSON") from error
    if not isinstance(data, dict):
        raise OllamaError("Ollama answered an unexpected JSON shape")
    return data


class OllamaClient:
    def __init__(
        self,
        host: str = "http://localhost:11434",
        model: str = "gemma4:e2b",
        timeout: float = 120.0,
        think: Optional[bool] = False,
        post: Optional[Transport] = None,
    ) -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.think = think
        self._post = post or _http_post

    def generate(self, prompt: str) -> str:
        """Return the final answer text for the prompt (never the thinking trace)."""
        payload: dict = {"model": self.model, "prompt": prompt, "stream": False}
        if self.think is not None:
            payload["think"] = self.think
        try:
            data = self._post(f"{self.host}/api/generate", payload, self.timeout)
        except OllamaError:
            raise
        except Exception as error:
            raise OllamaError(f"Ollama request failed: {error}") from error
        if not isinstance(data, dict):
            raise OllamaError("Ollama answered an unexpected shape")
        text = data.get("response")
        if not isinstance(text, str):
            raise OllamaError("Ollama reply has no 'response' text")
        return text
