import os

from cloudconvert_service import resolve_sandbox_mode


def test_sandbox_mode_defaults_to_live(monkeypatch):
    monkeypatch.delenv("CLOUDCONVERT_SANDBOX", raising=False)
    assert resolve_sandbox_mode() is False


def test_sandbox_mode_can_be_enabled_via_env(monkeypatch):
    monkeypatch.setenv("CLOUDCONVERT_SANDBOX", "true")
    assert resolve_sandbox_mode() is True
