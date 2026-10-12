"""Compulsory delivered sign-in codes and phone delivery.

These tests deliberately exercise the real auth service and server-rendered
forms.  A green result means a code was proven without ever making a session
before that proof, not that a real mail relay or SMS carrier was contacted.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import time
from types import SimpleNamespace

import pytest

from engineverse import auth, db, notify
from engineverse.config import reload_settings
from engineverse.security import otp, ratelimit, totp

PASSWORD = "Otp-Throwaway-Password-9!"


def _csrf(html: str) -> str:
    marker = 'name="csrf_token" value="'
    start = html.index(marker) + len(marker)
    return html[start : html.index('"', start)]


def _field(html: str, name: str) -> str:
    match = re.search(rf'name="{re.escape(name)}" value="([^"]*)"', html)
    assert match, name
    return match.group(1)


def _register(prefix: str = "otpuser") -> dict:
    tag = f"{prefix}{os.urandom(4).hex()}"
    return auth.register(
        email=f"{tag}@example.test",
        username=tag[:24],
        password=PASSWORD,
        full_name="OTP Throwaway",
        ip="203.0.113.10",
        user_agent="pytest",
    )


def _session_count(user_id: str) -> int:
    return int(db.scalar("SELECT count(*) AS c FROM sessions WHERE user_id = ?", user_id) or 0)


@pytest.fixture
def required_otp(monkeypatch):
    monkeypatch.setenv("ENGINEVERSE_LOGIN_OTP", "required")
    monkeypatch.delenv("ENGINEVERSE_SMTP_URL", raising=False)
    monkeypatch.delenv("ENGINEVERSE_SMS_URL", raising=False)
    reload_settings()
    yield
    # The shared conftest intentionally leaves old login tests password-only.
    os.environ["ENGINEVERSE_LOGIN_OTP"] = "disabled"
    os.environ.pop("ENGINEVERSE_SMTP_URL", None)
    os.environ.pop("ENGINEVERSE_SMS_URL", None)
    reload_settings()


def test_password_match_creates_no_session_before_the_code(client, seeded, required_otp):
    user = _register("nosession")
    before = _session_count(user["id"])
    page = client.get("/login")
    response = client.post(
        "/login",
        data={"csrf_token": _csrf(page.text), "identifier": user["email"], "password": PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code == 401
    assert _session_count(user["id"]) == before
    assert "We sent a 6-digit code to" in response.text
    assert "ev_session" not in response.headers.get("set-cookie", "")


def test_development_reveal_finishes_login_and_a_replay_is_refused(client, seeded, required_otp):
    user = _register("reveal")
    page = client.get("/login")
    challenge = client.post(
        "/login",
        data={"csrf_token": _csrf(page.text), "identifier": user["email"], "password": PASSWORD},
        follow_redirects=False,
    )
    token = _field(challenge.text, "otp_token")
    code = re.search(r'<code class="mono">([0-9]{6})</code>', challenge.text).group(1)
    done = client.post(
        "/login",
        data={"csrf_token": _csrf(challenge.text), "identifier": user["email"],
              "mfa_token": token, "otp": code},
        follow_redirects=False,
    )
    assert done.status_code == 303
    assert _session_count(user["id"]) == 1
    with pytest.raises(auth.AuthError) as caught:
        auth.login(identifier=user["email"], password="", mfa_token=token, otp=code)
    assert caught.value.code in {"otp_expired", "mfa_expired"}


def test_four_wrong_codes_count_down_and_the_fifth_consumes_the_challenge(seeded, required_otp):
    user = _register("countdown")
    with pytest.raises(auth.OtpRequired) as first:
        auth.login(identifier=user["email"], password=PASSWORD, ip="203.0.113.20")
    token = first.value.token
    assert first.value.attempts_left == 5
    for left in (4, 3, 2, 1):
        with pytest.raises(auth.OtpRequired) as caught:
            auth.login(identifier=user["email"], password="", mfa_token=token,
                       otp="000000", ip="203.0.113.20")
        assert caught.value.attempts_left == left
        assert caught.value.token == token
    with pytest.raises(auth.AuthError) as exhausted:
        auth.login(identifier=user["email"], password="", mfa_token=token,
                   otp="000000", ip="203.0.113.20")
    assert exhausted.value.code == "otp_exhausted"
    with pytest.raises(auth.AuthError) as refused:
        auth.login(identifier=user["email"], password="", mfa_token=token,
                   otp=first.value.revealed_code, ip="203.0.113.20")
    assert refused.value.code in {"otp_expired", "mfa_expired"}


def test_an_expired_code_returns_to_the_password_form(client, seeded, required_otp):
    user = _register("expired")
    page = client.get("/login")
    challenge = client.post(
        "/login", data={"csrf_token": _csrf(page.text), "identifier": user["email"], "password": PASSWORD},
        follow_redirects=False,
    )
    token = _field(challenge.text, "otp_token")
    db.execute("UPDATE security_challenges SET expires_at = 0 WHERE token_hash = ?", totp._challenge_hash(token))
    expired = client.post(
        "/login", data={"csrf_token": _csrf(challenge.text), "identifier": user["email"],
                         "mfa_token": token, "otp": "123456"}, follow_redirects=False,
    )
    assert expired.status_code == 401
    assert 'name="password"' in expired.text
    assert 'name="otp_token"' not in expired.text


def test_enrolled_totp_users_do_not_get_a_delivered_code(seeded, required_otp, monkeypatch):
    user = _register("totpfirst")
    secret = totp.random_secret()
    db.execute("UPDATE users SET totp_secret = ? WHERE id = ?", totp.pack(secret, []), user["id"])
    monkeypatch.setattr(notify, "send_login_otp", lambda *args, **kwargs: pytest.fail("OTP was delivered"))
    with pytest.raises(auth.MfaRequired):
        auth.login(identifier=user["email"], password=PASSWORD)
    db.execute("UPDATE users SET totp_secret = NULL WHERE id = ?", user["id"])


def test_verified_phone_can_use_sms_and_the_page_has_both_switch_options(
    client, seeded, required_otp, monkeypatch
):
    monkeypatch.setenv("ENGINEVERSE_SMTP_URL", "smtp://mail.example:587")
    monkeypatch.setenv("ENGINEVERSE_SMS_URL", "https://sms.example/send")
    reload_settings()
    user = _register("smschannel")
    auth.set_phone(user["id"], "+14155552671")
    db.execute("UPDATE users SET phone_verified = 1 WHERE id = ?", user["id"])
    sent = {}
    monkeypatch.setattr(notify, "send_login_otp", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        notify, "send_phone_otp",
        lambda to, code, minutes=5: sent.update(to=to, code=code) or True,
    )
    page = client.get("/login")
    response = client.post(
        "/login", data={"csrf_token": _csrf(page.text), "identifier": user["email"], "password": PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code == 401
    assert "+14155552671" not in response.text
    assert response.text.count('name="channel"') == 2
    token = _field(response.text, "otp_token")
    switched = client.post(
        "/login/otp/resend",
        data={"csrf_token": _csrf(response.text), "otp_token": token, "channel": "phone",
              "identifier": user["email"]},
        follow_redirects=False,
    )
    assert switched.status_code == 401
    assert "Text message" in switched.text
    assert sent["to"] == "+14155552671"
    assert sent["code"] not in switched.text


def test_switching_channels_replaces_the_old_code(seeded, required_otp, monkeypatch):
    monkeypatch.setenv("ENGINEVERSE_SMTP_URL", "smtp://mail.example:587")
    monkeypatch.setenv("ENGINEVERSE_SMS_URL", "https://sms.example/send")
    reload_settings()
    user = _register("switch")
    auth.set_phone(user["id"], "+14155552672")
    db.execute("UPDATE users SET phone_verified = 1 WHERE id = ?", user["id"])
    codes = []
    monkeypatch.setattr(notify, "send_login_otp", lambda email, code, minutes=5: codes.append(("email", code)) or True)
    monkeypatch.setattr(notify, "send_phone_otp", lambda phone, code, minutes=5: codes.append(("phone", code)) or True)
    with pytest.raises(auth.OtpRequired) as first:
        auth.login(identifier=user["email"], password=PASSWORD)
    second = auth.resend_login_otp(first.value.token, channel="phone")
    assert second.channel == "phone"
    with pytest.raises(auth.AuthError):
        auth.login(identifier=user["email"], password="", mfa_token=first.value.token, otp=codes[0][1])
    result = auth.login(identifier=user["email"], password="", mfa_token=second.token, otp=codes[-1][1])
    assert result[0]["id"] == user["id"]


def test_resend_cooldown_leaves_the_live_challenge_usable(seeded, required_otp):
    user = _register("cooldown")
    with pytest.raises(auth.OtpRequired) as first:
        auth.login(identifier=user["email"], password=PASSWORD)
    second = auth.resend_login_otp(first.value.token)
    with pytest.raises(auth.AuthError) as limited:
        auth.resend_login_otp(second.token)
    assert limited.value.code == "otp_rate_limited"
    result = auth.login(identifier=user["email"], password="", mfa_token=second.token,
                        otp=second.revealed_code)
    assert result[0]["id"] == user["id"]


def test_otp_issue_cap_returns_429(seeded, required_otp, monkeypatch):
    user = _register("issuecap")
    original = ratelimit.shared_check

    def blocked(key, limit, window_seconds, **kwargs):
        if key == f"otp-issue:{user['id']}":
            return ratelimit.RateLimitResult(False, 0, 900, limit)
        return original(key, limit, window_seconds, **kwargs)

    monkeypatch.setattr(ratelimit, "shared_check", blocked)
    with pytest.raises(auth.AuthError) as caught:
        auth.login(identifier=user["email"], password=PASSWORD)
    assert caught.value.status_code == 429
    assert caught.value.code == "otp_rate_limited"


def test_a_configured_but_failing_transport_fails_closed(seeded, required_otp, monkeypatch):
    monkeypatch.setenv("ENGINEVERSE_SMTP_URL", "smtp://mail.example:587")
    reload_settings()
    user = _register("transportfail")
    monkeypatch.setattr(notify, "send_login_otp", lambda *args, **kwargs: False)
    with pytest.raises(auth.AuthError) as caught:
        auth.login(identifier=user["email"], password=PASSWORD)
    assert caught.value.status_code == 503
    assert caught.value.code == "otp_undeliverable"
    assert db.query("SELECT * FROM security_challenges WHERE user_id = ? AND consumed_at IS NULL", user["id"]) == []
    assert "otp_revealed" not in caught.value.message


def test_production_never_reveals_a_code(seeded, required_otp, monkeypatch):
    monkeypatch.setenv("ENGINEVERSE_ENV", "production")
    reload_settings()
    user = _register("prodreveal")
    with pytest.raises(auth.AuthError) as caught:
        auth.login(identifier=user["email"], password=PASSWORD)
    assert caught.value.status_code == 503
    assert caught.value.code == "otp_undeliverable"
    assert db.query("SELECT * FROM security_challenges WHERE user_id = ? AND consumed_at IS NULL", user["id"]) == []


def test_production_problems_name_missing_transport_and_invalid_values(required_otp, monkeypatch):
    monkeypatch.setenv("ENGINEVERSE_ENV", "production")
    monkeypatch.setenv("ENGINEVERSE_SECRET", "production-secret-key-0123456789abcdefgh")
    monkeypatch.setenv("ENGINEVERSE_DB_URL", "postgresql://app:secret@example/engineverse")
    monkeypatch.setenv("ENGINEVERSE_SITE_URL", "https://engineverse.example")
    monkeypatch.setenv("ENGINEVERSE_JUDGE", "disabled")
    monkeypatch.setenv("ENGINEVERSE_LOGIN_OTP", "required")
    monkeypatch.delenv("ENGINEVERSE_SMTP_URL", raising=False)
    monkeypatch.delenv("ENGINEVERSE_SMS_URL", raising=False)
    reload_settings()
    assert any("ENGINEVERSE_LOGIN_OTP=required" in item for item in reload_settings().production_problems())
    monkeypatch.setenv("ENGINEVERSE_LOGIN_OTP", "sometimes")
    reload_settings()
    assert any("ENGINEVERSE_LOGIN_OTP" in item and "required" in item for item in get_problems())


def get_problems() -> list[str]:
    from engineverse.config import get_settings

    return get_settings().production_problems()


def test_disabled_mode_is_password_only(seeded, monkeypatch):
    monkeypatch.setenv("ENGINEVERSE_LOGIN_OTP", "disabled")
    reload_settings()
    user = _register("disabled")
    logged, cookie, session_id = auth.login(identifier=user["email"], password=PASSWORD)
    assert logged["id"] == user["id"]
    assert cookie and session_id


def test_phone_changes_are_password_gated(seeded, required_otp):
    user = _register("phonegate")
    with pytest.raises(auth.AuthError) as caught:
        auth.set_phone(user["id"], "+14155552673", "wrong-password")
    assert caught.value.status_code == 403
    assert db.query_one("SELECT phone FROM users WHERE id = ?", user["id"])["phone"] is None
    auth.set_phone(user["id"], "+14155552673", PASSWORD)
    assert db.query_one("SELECT phone FROM users WHERE id = ?", user["id"])["phone"] == "+14155552673"


def test_phone_save_text_verify_remove_round_trip(seeded, required_otp, monkeypatch):
    monkeypatch.setenv("ENGINEVERSE_SMS_URL", "https://sms.example/send")
    reload_settings()
    user = _register("phoneround")
    auth.set_phone(user["id"], "+14155552674", PASSWORD)
    sent = {}
    monkeypatch.setattr(notify, "send_phone_otp", lambda to, code, minutes=10: sent.update(code=code) or True)
    token = auth.start_phone_verification(user["id"])
    assert sent and "14155552674" not in (otp.mask_phone("+14155552674"))
    with pytest.raises(auth.AuthError):
        auth.confirm_phone_verification(user["id"], token, "000000")
    assert auth.confirm_phone_verification(user["id"], token, sent["code"])
    row = db.query_one("SELECT phone, phone_verified FROM users WHERE id = ?", user["id"])
    assert row["phone"] == "+14155552674" and int(row["phone_verified"]) == 1
    auth.remove_phone(user["id"], PASSWORD)
    row = db.query_one("SELECT phone, phone_verified FROM users WHERE id = ?", user["id"])
    assert row["phone"] is None and int(row["phone_verified"]) == 0


def test_phone_uniqueness_uses_a_vague_refusal(seeded, required_otp):
    first, second = _register("phoneone"), _register("phonetwo")
    auth.set_phone(first["id"], "+14155552675", PASSWORD)
    with pytest.raises(auth.AuthError) as caught:
        auth.set_phone(second["id"], "+14155552675", PASSWORD)
    assert caught.value.code == "phone_taken"
    assert "+14155552675" not in caught.value.message


def test_phone_validation_requires_e164_and_refuses_letters(required_otp):
    valid = ["(+1) 415-555-2676", "+919876543210"]
    for value in valid:
        normalized = __import__("engineverse.security.validators", fromlist=["normalize_phone"]).normalize_phone(value)
        assert normalized.startswith("+")
    invalid = ["4155552676", "+0123456789", "+123", "+1234567890123456", "+1-415-ABC-2676"]
    validators = __import__("engineverse.security.validators", fromlist=["validate_phone"])
    for value in invalid:
        with pytest.raises(validators.ValidationError):
            validators.validate_phone(value)


def test_code_storage_is_keyed_and_secret_rotation_kills_it(seeded, required_otp, monkeypatch):
    user = _register("rotation")
    with pytest.raises(auth.OtpRequired) as caught:
        auth.login(identifier=user["email"], password=PASSWORD)
    row = db.query_one("SELECT payload FROM security_challenges WHERE user_id = ?", user["id"])
    payload = totp.unseal(row["payload"])
    assert caught.value.revealed_code not in row["payload"]
    expected = hmac.new(
        b"test-secret-key-for-pytest-only-0123456789",
        caught.value.revealed_code.encode(), hashlib.sha256,
    ).hexdigest()
    assert payload["code_hash"] == expected
    monkeypatch.setenv("ENGINEVERSE_SECRET", "rotated-secret-key-0123456789abcdefgh")
    reload_settings()
    with pytest.raises(auth.AuthError):
        auth.login(identifier=user["email"], password="", mfa_token=caught.value.token,
                   otp=caught.value.revealed_code)


def test_email_and_phone_masks_use_bullets():
    assert "•" in otp.mask_email("alice@example.com")
    assert "alice@example.com" not in otp.mask_email("alice@example.com")
    assert "•" in otp.mask_phone("+14155552677")
    assert "+14155552677" not in otp.mask_phone("+14155552677")
    assert otp.mask_phone("+14155552677").endswith("2677")


def test_sms_gateway_contract_strips_userinfo_and_uses_bearer(required_otp, monkeypatch):
    monkeypatch.setenv("ENGINEVERSE_SMS_URL", "https://operator:bearer-secret@sms.example:8443/send")
    reload_settings()
    seen = {}

    class Response:
        status = 202

        def close(self):
            pass

    def fake_urlopen(request, timeout=0):
        seen["url"] = request.full_url
        seen["authorization"] = request.get_header("Authorization")
        seen["body"] = json.loads(request.data.decode())
        return Response()

    monkeypatch.setattr(notify.urllib_request, "urlopen", fake_urlopen)
    assert notify.send_sms("+14155552678", "a code")
    assert seen == {
        "url": "https://sms.example:8443/send",
        "authorization": "Bearer bearer-secret",
        "body": {"to": "+14155552678", "body": "a code"},
    }
    monkeypatch.setenv("ENGINEVERSE_ENV", "production")
    monkeypatch.setenv("ENGINEVERSE_SMS_URL", "http://operator:secret@sms.example/send")
    reload_settings()
    assert notify.send_sms("+14155552678", "a code") is False
    monkeypatch.setattr(notify.urllib_request, "urlopen", lambda *args, **kwargs: (_ for _ in ()).throw(OSError("down")))
    monkeypatch.setenv("ENGINEVERSE_ENV", "test")
    reload_settings()
    assert notify.send_sms("+14155552678", "a code") is False


def test_audit_records_otp_events_without_the_code(seeded, required_otp):
    user = _register("auditotp")
    with pytest.raises(auth.OtpRequired) as caught:
        auth.login(identifier=user["email"], password=PASSWORD)
    code = caught.value.revealed_code
    rows = db.query("SELECT action, meta FROM audit_logs WHERE actor_id = ? ORDER BY created_at", user["id"])
    assert rows
    assert all(code not in str(row) for row in rows)


def test_two_devices_see_profile_changes_and_only_the_other_session_can_be_revoked(app, seeded, monkeypatch):
    monkeypatch.setenv("ENGINEVERSE_LOGIN_OTP", "disabled")
    reload_settings()
    user = _register("devices")
    from starlette.testclient import TestClient

    with TestClient(app, raise_server_exceptions=False) as client_a, TestClient(app, raise_server_exceptions=False) as client_b:
        for client in (client_a, client_b):
            page = client.get("/login")
            response = client.post(
                "/login", data={"csrf_token": _csrf(page.text), "identifier": user["email"], "password": PASSWORD},
                follow_redirects=False,
            )
            assert response.status_code == 303
        settings_a = client_a.get("/settings")
        saved = client_a.post(
            "/settings/profile",
            data={"csrf_token": _csrf(settings_a.text), "full_name": "Changed on A", "headline": "", "bio": "",
                  "country": "", "github_url": "", "linkedin_url": "", "portfolio_url": "", "weekly_study_hours": "7"},
            follow_redirects=False,
        )
        assert saved.status_code == 303
        assert db.query_one("SELECT full_name FROM profiles WHERE user_id = ?", user["id"])["full_name"] == "Changed on A"
        settings_b = client_b.get("/settings")
        assert "Changed on A" in settings_b.text
        assert settings_b.text.count('action="/settings/sessions/revoke"') == 1
