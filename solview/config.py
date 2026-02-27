"""Centralized runtime configuration for the solview library."""

from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING

from solview.settings import SolviewSettings

if TYPE_CHECKING:
    from fastapi import FastAPI

_settings_lock = RLock()
_settings_instance: SolviewSettings | None = None


def setup_solview(
    settings: SolviewSettings | None = None,
    *,
    app: "FastAPI | None" = None,
    setup_logger: bool = True,
    setup_tracer: bool = True,
    **overrides,
) -> SolviewSettings:
    """
    Configure and store a single SolviewSettings instance for the process.

    Optionally runs setup_logger() and, when ``app`` is provided, setup_tracer(app),
    so the FastAPI app can be fully initialized with a single call.

    Args:
        settings: Pre-built SolviewSettings instance, or None to build from overrides/env.
        app: Optional FastAPI app. If given and setup_tracer is True, setup_tracer(app) is called.
        setup_logger: If True (default), call setup_logger() after storing settings.
        setup_tracer: If True (default) and ``app`` is provided, call setup_tracer(app).
        **overrides: Keyword arguments to build SolviewSettings when ``settings`` is None.

    Returns:
        The stored SolviewSettings instance.

    Example:
        settings = SolviewSettings(service_name="my-api")
        app = FastAPI()
        configure_solview(settings, app=app)  # one call: config + logger + tracer
    """
    global _settings_instance

    if settings is not None and overrides:
        raise ValueError(
            "Use either 'settings' or keyword overrides, not both."
        )

    resolved = settings or SolviewSettings(**overrides)
    with _settings_lock:
        _settings_instance = resolved

    if setup_logger:
        from solview.solview_logging import setup_logger as _setup_logger
        _setup_logger()

    if setup_tracer:
        from solview.tracing.core import setup_tracer as _setup_tracer
        _setup_tracer(app)

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
