"""The leftovers that can be checked without Docker, a browser, or a live Judge0."""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from engineverse.judge import provider_info
from engineverse.judge.isolation import probe
from scripts.prepare_listing import listing_text

ROOT = Path(__file__).resolve().parents[2]


class _Quiet(BaseHTTPRequestHandler):
    body = b""

    def do_POST(self):
        payload = self.body
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, *_args):
        return


def _serve(stdout: str) -> tuple[HTTPServer, str]:
    class Handler(_Quiet):
        body = json.dumps({"stdout": stdout}).encode()

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def test_unconfigured_judge_is_not_isolated():
    result = probe("")
    assert result["isolated"] is False
    assert result["canary_held"] is False
    assert "not" in result["sentence"].lower()


def test_a_held_canary_is_still_not_a_certification():
    server, url = _serve("CANARY_OK\nSECRET:absent\nPASSWD:blocked\n")
    try:
        result = probe(url, timeout=2)
    finally:
        server.shutdown()
    assert result["canary_held"] is True
    assert result["isolated"] is False
    assert "not a certification" in result["sentence"]


def test_a_leaked_secret_is_not_isolated():
    server, url = _serve("CANARY_OK\nSECRET:present\nPASSWD:blocked\n")
    try:
        result = probe(url, timeout=2)
    finally:
        server.shutdown()
    assert result["secret_leaked"] is True
    assert result["isolated"] is False
    assert result["canary_held"] is False


def test_judge0_provider_info_cannot_say_verified(monkeypatch):
    class Fake:
        name = "judge0"
        available = True

    monkeypatch.setattr("engineverse.judge.resolve_provider", lambda: Fake())
    info = provider_info()
    assert info["isolation_verified"] is False
    assert "does not verify" in info["isolation"]


def test_listing_text_stays_free_and_unsubmitted():
    text = listing_text("EngineVerse")
    blob = " ".join(text.values()).lower()
    assert text["submitted"] == "false"
    assert text["play_approved"] == "false"
    assert "not accredited" in blob
    assert "play approved" not in blob
    assert "published on google play" not in blob
    assert len(text["title"]) <= 30
    assert len(text["short_description"]) <= 80


def test_listing_name_is_the_argument_not_a_hardcoded_rename():
    text = listing_text("North Lab")
    assert text["title"] == "North Lab"
    assert "ENGINEERX" not in text["full_description"]


def test_committed_listing_pack_is_not_a_submission():
    pack = ROOT / "android" / "listing"
    data = json.loads((pack / "listing.json").read_text(encoding="utf-8"))
    assert data["submitted"] == "false"
    assert data["play_approved"] == "false"
    icon = (pack / "icon-512.png").read_bytes()
    graphic = (pack / "feature-graphic.png").read_bytes()
    assert icon[1:4] == b"PNG"
    assert graphic[1:4] == b"PNG"
    width = int.from_bytes(graphic[16:20], "big")
    height = int.from_bytes(graphic[20:24], "big")
    assert (width, height) == (1024, 500)
