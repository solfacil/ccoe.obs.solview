import os
from solview.settings import SolviewSettings
from solview.solview_logging.settings import LoggingSettings

def test_solview_settings_env(monkeypatch):
    monkeypatch.setenv("SOLVIEW_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("SOLVIEW_ENVIRONMENT", "homolog")
    monkeypatch.setenv("SOLVIEW_SERVICE_NAME", "api-sol")
    monkeypatch.setenv("SOLVIEW_DOMAIN", "solar_os")
    monkeypatch.setenv("SOLVIEW_SUBDOMAIN", "obs")
    monkeypatch.setenv("SOLVIEW_VERSION", "9.9.9")

    # Força o reload do módulo para recarregar as envs após o monkeypatch
    import importlib
    import solview.settings
    importlib.reload(solview.settings)
    from solview.settings import SolviewSettings
    
    s = SolviewSettings()
    assert s.log_level == "DEBUG"
    assert s.environment == "homolog"
    assert s.service_name == "api-sol"
    assert s.domain == "solar_os"
    assert s.subdomain == "obs"
    assert s.version == "9.9.9"
    assert s.service_name_composed == "homolog-api-sol"

def test_logging_settings_properties():
    s = LoggingSettings(
        log_level="WARNING", environment="prod", service_name="svc", domain="dm", subdomain="sd", version="2.0"
    )
    assert s.log_level == "WARNING"
    assert s.service_name_composed == "prod-svc"
    assert s.domain == "dm"
    assert s.subdomain == "sd"
    assert s.version == "2.0"