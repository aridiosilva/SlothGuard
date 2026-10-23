"""OllamaClient: request format, thinking switch and error handling.

Most tests use a fake transport. The last group talks to a tiny local HTTP server to
exercise the real network code without needing Ollama.
"""
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from slothguard.llm import OllamaClient, OllamaError


class FakePost:
    def __init__(self, reply=None, error=None):
        self.reply = reply if reply is not None else {"response": "ok", "done": True}
        self.error = error
        self.calls = []

    def __call__(self, url, payload, timeout):
        self.calls.append((url, payload, timeout))
        if self.error:
            raise self.error
        return self.reply


def test_posts_to_the_generate_endpoint():
    post = FakePost()
    OllamaClient(host="http://localhost:11434", model="gemma4:e2b", post=post).generate("hi")
    assert post.calls[0][0] == "http://localhost:11434/api/generate"


def test_trailing_slash_in_host_is_ignored():
    post = FakePost()
    OllamaClient(host="http://example.test:1234/", model="m", post=post).generate("hi")
    assert post.calls[0][0] == "http://example.test:1234/api/generate"


def test_payload_disables_streaming_and_thinking_by_default():
    post = FakePost()
    OllamaClient(host="http://h", model="gemma4:e2b", post=post).generate("explain this")
    payload = post.calls[0][1]
    assert payload["model"] == "gemma4:e2b"
    assert payload["prompt"] == "explain this"
    assert payload["stream"] is False
    assert payload["think"] is False


def test_thinking_can_be_enabled():
    post = FakePost()
    OllamaClient(host="http://h", model="m", think=True, post=post).generate("hi")
    assert post.calls[0][1]["think"] is True


def test_thinking_field_is_omitted_when_none():
    post = FakePost()
    OllamaClient(host="http://h", model="m", think=None, post=post).generate("hi")
    assert "think" not in post.calls[0][1]


def test_timeout_is_passed_to_the_transport():
    post = FakePost()
    OllamaClient(host="http://h", model="m", timeout=5, post=post).generate("hi")
    assert post.calls[0][2] == 5


def test_returns_only_the_final_answer_not_the_thinking_trace():
    post = FakePost(reply={"response": "Final answer.", "thinking": "long reasoning...", "done": True})
    assert OllamaClient(host="http://h", model="m", post=post).generate("hi") == "Final answer."


def test_reply_without_a_response_text_is_an_error():
    post = FakePost(reply={"done": True})
    with pytest.raises(OllamaError):
        OllamaClient(host="http://h", model="m", post=post).generate("hi")


def test_non_text_response_is_an_error():
    post = FakePost(reply={"response": 42})
    with pytest.raises(OllamaError):
        OllamaClient(host="http://h", model="m", post=post).generate("hi")


def test_any_transport_failure_is_reported_as_ollama_error():
    post = FakePost(error=ConnectionError("refused"))
    with pytest.raises(OllamaError):
        OllamaClient(host="http://h", model="m", post=post).generate("hi")


# ---- real network code, against a local fake server ----

def _serve(handler_cls):
    server = HTTPServer(("127.0.0.1", 0), handler_cls)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def _make_handler(status=200, body=b'{"response": "from server", "done": true}', record=None):
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            length = int(self.headers.get("Content-Length", 0))
            if record is not None:
                record["path"] = self.path
                record["content_type"] = self.headers.get("Content-Type")
                record["body"] = json.loads(self.rfile.read(length).decode("utf-8"))
            else:
                self.rfile.read(length)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    return Handler


def test_real_transport_sends_json_and_parses_the_reply():
    seen = {}
    server, host = _serve(_make_handler(record=seen))
    try:
        answer = OllamaClient(host=host, model="gemma4:e2b").generate("hello")
    finally:
        server.shutdown()
    assert answer == "from server"
    assert seen["path"] == "/api/generate"
    assert seen["content_type"] == "application/json"
    assert seen["body"] == {"model": "gemma4:e2b", "prompt": "hello", "stream": False, "think": False}


def test_real_transport_reports_http_errors():
    server, host = _serve(_make_handler(status=500, body=b'{"error": "boom"}'))
    try:
        with pytest.raises(OllamaError):
            OllamaClient(host=host, model="m").generate("hello")
    finally:
        server.shutdown()


def test_real_transport_reports_invalid_json():
    server, host = _serve(_make_handler(body=b"not json"))
    try:
        with pytest.raises(OllamaError):
            OllamaClient(host=host, model="m").generate("hello")
    finally:
        server.shutdown()


def test_real_transport_reports_a_closed_port():
    probe = socket.socket()
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    with pytest.raises(OllamaError):
        OllamaClient(host=f"http://127.0.0.1:{port}", model="m", timeout=2).generate("hello")
