"""Centralized runtime configuration for the solview library."""

from __future__ import annotations

from threading import RLock

from solview.settings import SolviewSettings

_settings_lock = RLock()
_settings_instance: SolviewSettings | None = None


def configure_solview(
    settings: SolviewSettings | None = None,
    **overrides,
) -> SolviewSettings:
    """
    Configure and store a single SolviewSettings instance for the process.

    Either pass a pre-built ``settings`` instance OR keyword overrides.
    """
    global _settings_instance

    if settings is not None and overrides:
        raise ValueError(
            "Use either 'settings' or keyword overrides, not both."
        )

    resolved = settings or SolviewSettings(**overrides)
    with _settings_lock:
        _settings_instance = resolved
    return resolved


def get_settings() -> SolviewSettings:
    """
    Return the configured settings singleton.

    If it was not configured yet, initialize it lazily from environment.
    """
    global _settings_instance

    if _settings_instance is None:
        with _settings_lock:
            if _settings_instance is None:
                _settings_instance = SolviewSettings()

    return _settings_instance
