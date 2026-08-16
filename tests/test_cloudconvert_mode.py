import os

from cloudconvert_service import resolve_api_key, resolve_sandbox_mode
from turnstile import verify


def test_sandbox_mode_defaults_to_live(monkeypatch):
    monkeypatch.delenv("CLOUDCONVERT_SANDBOX", raising=False)
    assert resolve_sandbox_mode() is False


def test_sandbox_mode_can_be_enabled_via_env(monkeypatch):
    monkeypatch.setenv("CLOUDCONVERT_SANDBOX", "true")
    assert resolve_sandbox_mode() is True


def test_live_api_key_is_selected_by_default(monkeypatch):
    monkeypatch.delenv("CLOUDCONVERT_SANDBOX", raising=False)
    monkeypatch.setenv("CLOUDCONVERT_LIVE_API_KEY", "live-key")
    monkeypatch.delenv("CLOUDCONVERT_SANDBOX_API_KEY", raising=False)
    assert resolve_api_key() == "live-key"


def test_sandbox_api_key_is_selected_when_sandbox_mode_is_enabled(monkeypatch):
    monkeypatch.setenv("CLOUDCONVERT_SANDBOX", "true")
    monkeypatch.setenv("CLOUDCONVERT_SANDBOX_API_KEY", "sandbox-key")
    monkeypatch.delenv("CLOUDCONVERT_LIVE_API_KEY", raising=False)
    assert resolve_api_key() == "sandbox-key"


def test_turnstile_verification_requires_success_action_and_hostname(monkeypatch):
    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"success": True, "action": "upload", "hostname": "localhost"}

    monkeypatch.setenv("TURNSTILE_SECRET", "secret")
    monkeypatch.setenv("TURNSTILE_HOSTNAMES", "localhost")
    monkeypatch.setattr("turnstile.requests.post", lambda *args, **kwargs: Response())

    assert verify("token", "127.0.0.1") is True


def test_turnstile_verification_rejects_wrong_action(monkeypatch):
    class Response:
        def raise_for_status(self):
            pass

        def json(self):
            return {"success": True, "action": "other", "hostname": "localhost"}

    monkeypatch.setenv("TURNSTILE_SECRET", "secret")
    monkeypatch.setenv("TURNSTILE_HOSTNAMES", "localhost")
    monkeypatch.setattr("turnstile.requests.post", lambda *args, **kwargs: Response())

    assert verify("token") is False
