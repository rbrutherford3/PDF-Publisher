import os

from cloudconvert_service import resolve_api_key, resolve_sandbox_mode


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
