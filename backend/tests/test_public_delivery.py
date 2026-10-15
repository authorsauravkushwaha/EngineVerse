"""Pages handoff, signed Android link and private encrypted off-site backup."""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from starlette.testclient import TestClient

from engineverse.config import reload_settings
from engineverse.distribution import normalise_apk_url
from scripts import export_pages, verify_apk_release, verify_hosted_app, verify_pages, verify_twa

ROOT = Path(__file__).resolve().parents[2]
APK = "https://github.com/authorsauravkushwaha/EngineVerse/releases/download/android-v1.2.3/EngineVerse.apk"
ORIGIN = "https://learn.example.org"
FINGERPRINT = ":".join(["A1"] * 32)


def test_apk_url_is_versioned_and_owned_by_this_repo():
    assert normalise_apk_url("") == ""
    assert normalise_apk_url(APK) == APK
    for invalid in (
        "https://evil.example/EngineVerse.apk", "javascript:alert(1)",
        "https://github.com/other/EngineVerse/releases/download/android-v1.2.3/EngineVerse.apk",
        APK + "?redirect=evil", APK.replace("android-v1.2.3", "../android-v1.2.3"),
        APK.replace("EngineVerse.apk", "debug.apk"),
    ):
        with pytest.raises(ValueError):
            normalise_apk_url(invalid)


def test_install_is_public_even_when_catalogue_requires_signin(seeded, monkeypatch):
    monkeypatch.setenv("ENGINEVERSE_SIGNIN", "required")
    monkeypatch.delenv("ENGINEVERSE_APK_URL", raising=False)
    reload_settings()
    from main import create_app
    try:
        with TestClient(create_app(), follow_redirects=False) as web:
            page = web.get("/install")
            assert page.status_code == 200
            assert "No signed APK has been published" in page.text
            assert "Download EngineVerse.apk" not in page.text
            assert web.get("/explore").status_code == 303
            assert web.get("/.well-known/assetlinks.json").status_code == 404
    finally:
        monkeypatch.undo()
        reload_settings()


def test_only_the_approved_apk_is_advertised(seeded, monkeypatch):
    from main import create_app
    monkeypatch.setenv("ENGINEVERSE_APK_URL", APK)
    reload_settings()
    try:
        with TestClient(create_app()) as web:
            assert f'href="{APK}"' in web.get("/install").text
        monkeypatch.setenv("ENGINEVERSE_APK_URL", "https://evil.example/download.apk")
        settings = reload_settings()
        assert not settings.approved_apk_url
        monkeypatch.setenv("ENGINEVERSE_ENV", "production")
        assert any("ENGINEVERSE_APK_URL" in error for error in reload_settings().production_problems())
    finally:
        monkeypatch.undo()
        reload_settings()


def test_gateway_keeps_paths_and_never_claims_a_release_without_one(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)
    site = tmp_path / "site"
    export_pages.export_gateway(site, "/EngineVerse/", ORIGIN)
    manifest = json.loads((site / "deployment.json").read_text())
    assert manifest == {"revision": "a" * 40, "mode": "gateway",
                        "base": "/EngineVerse/", "app_url": ORIGIN}
    home = (site / "index.html").read_text()
    moved = (site / "404.html").read_text()
    assert f'href="{ORIGIN}/"' in home
    assert f'href="{ORIGIN}/install"' in home
    assert "Download signed" not in home
    assert "location.replace(app+path+location.search+location.hash)" in moved
    assert "/EngineVerse/static/css/app.css" in home
    assert "Not hosted yet" in export_pages.gateway_page("/EngineVerse/", "", "EngineVerse")
    assert "there is no APK download here" in export_pages.reading_copy_install_main(ORIGIN)
    assert "Download signed" not in export_pages.reading_copy_install_main(ORIGIN)
    export_pages.export_gateway(site, "/EngineVerse/", ORIGIN, apk_url=APK)
    assert f'href="{APK}"' in (site / "index.html").read_text()
    assert f'href="{APK}"' in (site / "404.html").read_text()


@pytest.mark.skipif(not shutil.which("node"), reason="Node is required to test the browser redirect")
def test_old_pages_bookmark_opens_same_page_on_host_and_not_on_another_origin():
    page = export_pages.gateway_page("/EngineVerse/", ORIGIN, "EngineVerse", not_found=True)
    script = re.search(r"<script>(.*?)</script>", page, flags=re.S).group(1)
    program = """
const vm = require('node:vm');
const script = %s;
function target(path, search='') {
  let result = null;
  const location = { pathname: path, search, hash: '#section', replace: (value) => result = value };
  vm.runInNewContext(script, { location });
  return result;
}
if (target('/EngineVerse/topics/ohms-law/', '?depths=all') !==
    'https://learn.example.org/topics/ohms-law/?depths=all#section') process.exit(1);
if (target('/EngineVerseEvil/topics/ohms-law/') !== null) process.exit(2);
if (target('/EngineVerse/../outside/') !== 'https://learn.example.org/#section') process.exit(3);
""" % json.dumps(script)
    result = subprocess.run(["node", "-e", program], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_pages_verifier_checks_gateway_mode_sha_and_links(monkeypatch):
    page = export_pages.gateway_page("/EngineVerse/", ORIGIN, "EngineVerse")
    moved = export_pages.gateway_page("/EngineVerse/", ORIGIN, "EngineVerse", not_found=True)
    sha = "b" * 40

    def fake_fetch(url, _sha, _attempt, _content_type):
        if url.endswith("deployment.json"):
            return json.dumps({"revision": sha, "mode": "gateway", "app_url": ORIGIN})
        if url.endswith("404.html"):
            return moved
        if url.endswith("app.css"):
            return "body { color: #fff; }"
        return page

    monkeypatch.setattr(verify_pages, "_fetch", fake_fetch)
    verify_pages.verify("https://user.github.io/EngineVerse/", sha, mode="gateway",
                        app_url=ORIGIN, attempts=1, delay=0)
    with pytest.raises(SystemExit, match="expected Pages mode"):
        verify_pages.verify("https://user.github.io/EngineVerse/", sha,
                            mode="reading-copy", attempts=1, delay=0)
    with pytest.raises(SystemExit, match="not pointing"):
        verify_pages.verify("https://user.github.io/EngineVerse/", sha, mode="gateway",
                            app_url="https://other.example.org", attempts=1, delay=0)


def _host_response(_origin, path):
    if path == "/health":
        return "application/json", json.dumps({"ok": True, "brand": "EngineVerse"})
    if path == "/manifest.webmanifest":
        return "application/manifest+json", json.dumps({
            "start_url": "/", "scope": "/", "icons": [{"src": "/static/icons/icon-512.png"}]
        })
    if path == "/login":
        return "text/html", '<form action="/login"></form>'
    if path == "/register":
        return "text/html", '<form action="/register"></form>'
    if path == "/install":
        return "text/html", "<h1>Android</h1>"
    raise ValueError(path)


def test_gateway_requires_a_real_production_app_with_open_registration():
    verify_hosted_app.verify(ORIGIN, get=_host_response)
    def development(origin, path):
        if path == "/health":
            return "application/json", json.dumps({"ok": True, "brand": "EngineVerse", "users": 1})
        return _host_response(origin, path)
    with pytest.raises(ValueError, match="development-only"):
        verify_hosted_app.verify(ORIGIN, get=development)
    def closed(origin, path):
        if path == "/register":
            return "text/html", "Registration closed"
        return _host_response(origin, path)
    with pytest.raises(ValueError, match="register"):
        verify_hosted_app.verify(ORIGIN, get=closed)
    with pytest.raises(ValueError, match="HTTPS"):
        verify_hosted_app.verify("http://localhost:8000", get=_host_response)


def test_digital_asset_links_must_match_the_actual_signing_key():
    def get(_origin, _path):
        return "application/json", json.dumps([{
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {"namespace": "android_app", "package_name": "org.engineverse.app",
                       "sha256_cert_fingerprints": [FINGERPRINT]},
        }])
    verify_twa.verify(ORIGIN, "org.engineverse.app", FINGERPRINT, get=get)
    with pytest.raises(ValueError, match="do not match"):
        verify_twa.verify(ORIGIN, "org.engineverse.app", ":".join(["AB"] * 32), get=get)
    with pytest.raises(ValueError, match="required"):
        verify_twa.verify(ORIGIN, "bad package", FINGERPRINT, get=get)


def test_pages_never_advertises_a_missing_or_draft_apk_release():
    commands = []
    def run(args, **_kwargs):
        commands.append(args)
        return SimpleNamespace(returncode=0, stdout=json.dumps({
            "assets": [{"name": "EngineVerse.apk", "size": 100}], "isDraft": False,
        }))
    verify_apk_release.verify(APK, run=run)
    assert commands[0][3] == "android-v1.2.3"
    with pytest.raises(ValueError):
        verify_apk_release.verify("https://evil.example/app.apk", run=run)
    def draft(_args, **_kwargs):
        return SimpleNamespace(returncode=0, stdout=json.dumps({
            "assets": [{"name": "EngineVerse.apk", "size": 100}], "isDraft": True,
        }))
    with pytest.raises(ValueError, match="nonempty"):
        verify_apk_release.verify(APK, run=draft)


def test_encrypted_backup_requires_private_repo_and_uploads_only_ciphertext(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "release-args"
    (bin_dir / "gh").write_text(
        '#!/bin/sh\nif [ "$1" = repo ]; then echo "${TEST_PRIVATE:-true}"; exit 0; fi\n'
        'for arg in "$@"; do case "$arg" in *.age)\n'
        '  [ -s "$arg" ] && ! grep -q "private-learner" "$arg" || exit 8;; esac; done\n'
        'printf "%s\\n" "$@" > "$TEST_RELEASE_ARGS"\n', encoding="utf-8",
    )
    (bin_dir / "pg_dump").write_text('#!/bin/sh\nprintf "private-learner@example.org"\n', encoding="utf-8")
    (bin_dir / "age").write_text(
        '#!/bin/sh\n[ "$1" = -r ] && [ "$3" = -o ] || exit 8\ncat >/dev/null\n'
        'head -c 80 /dev/zero | tr "\\000" X > "$4"\n', encoding="utf-8",
    )
    for path in bin_dir.iterdir():
        path.chmod(0o755)
    temp = tmp_path / "private-temp"
    temp.mkdir()
    env = {**os.environ, "PATH": f"{bin_dir}:{os.environ.get('PATH', '')}",
           "TEST_RELEASE_ARGS": str(log), "TMPDIR": str(temp),
           "ENGINEVERSE_BACKUP_REPO": "operator/engineverse-private-backups",
           "ENGINEVERSE_BACKUP_AGE_RECIPIENT": "age1recipient-for-test",
           "GH_TOKEN": "private-gh-token-never-print", "PGHOST": "db", "PGUSER": "backup",
           "PGDATABASE": "engineverse", "PGPASSWORD": "private-db-password-never-print"}
    result = subprocess.run(["bash", "scripts/backup_github.sh"], cwd=ROOT,
                            env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "release\ncreate\nengineverse-backup-" in log.read_text()
    assert "private-learner" not in log.read_text() + result.stdout + result.stderr
    assert "private-db-password" not in result.stdout + result.stderr
    assert "private-gh-token" not in result.stdout + result.stderr
    assert list(temp.iterdir()) == [], "temporary ciphertext must be removed after upload"
    log.unlink()
    env["TEST_PRIVATE"] = "false"
    refused = subprocess.run(["bash", "scripts/backup_github.sh"], cwd=ROOT,
                             env=env, capture_output=True, text=True)
    assert refused.returncode != 0
    assert "not private" in refused.stderr
    assert not log.exists(), "a public repository must never receive a release"
    # If pg_dump emitted bytes and THEN failed, pipefail must still refuse an
    # apparently encrypted but incomplete archive; nothing is uploaded.
    env["TEST_PRIVATE"] = "true"
    (bin_dir / "pg_dump").write_text(
        '#!/bin/sh\nprintf "partial-private-learner@example.org"\nexit 3\n', encoding="utf-8"
    )
    incomplete = subprocess.run(["bash", "scripts/backup_github.sh"], cwd=ROOT,
                                env=env, capture_output=True, text=True)
    assert incomplete.returncode != 0 and not log.exists()
    assert list(temp.iterdir()) == []


@pytest.mark.skipif(not shutil.which("node"), reason="Node is required for the TWA build self-check")
def test_twa_generator_refuses_to_point_at_the_pages_or_an_untrusted_host():
    result = subprocess.run(["node", "android/build-twa.cjs", "--self-check"], cwd=ROOT,
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    assert "self-check ok" in result.stdout


def test_public_compose_keeps_postgres_private_and_does_not_commit_credentials():
    edge = (ROOT / "deploy" / "public.yml").read_text()
    caddy = (ROOT / "deploy" / "Caddyfile").read_text()
    github = (ROOT / "deploy" / "github-backups.yml").read_text()
    base = (ROOT / "deploy" / "docker-compose.yml").read_text()
    assert "80:80" in edge and "443:443" in edge
    assert "header_up X-Forwarded-For {remote_host}" in caddy
    assert "ENGINEVERSE_APK_URL" in base and "ENGINEVERSE_TWA_SHA256" in base
    assert "PGUSER: engineverse_app" in github and "ENGINEVERSE_BACKUP_GH_TOKEN:?" in github
    assert "networks: [internal, backup-egress]" in github
    assert '127.0.0.1:8000:8000' in base and '"5432:5432"' not in base
