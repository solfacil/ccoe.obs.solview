from solview.solview_logging.settings import LoggingSettings

def test_service_name_composed_default():
    s = LoggingSettings()
    assert s.service_name == "app"
    assert s.environment == "development"
    assert s.service_name_composed == "development-app"

def test_service_name_composed_with_custom_values():
    s = LoggingSettings(
        service_name="pricing-api",
        environment="prd",
        log_level="INFO",
        domain="solar",
        subdomain="checkout",
        version="9.9.9"
    )
    assert s.service_name_composed == "prd-pricing-api"
    assert s.log_level == "INFO"
    assert s.domain == "solar"
    assert s.subdomain == "checkout"
    assert s.version == "9.9.9"

def test_service_name_composed_empty_values():
    s = LoggingSettings(service_name="", environment="")
    assert s.service_name_composed == "-"
