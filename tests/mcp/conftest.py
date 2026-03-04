import pytest
from solview.settings import SolviewSettings
from solview.config import setup_settings


@pytest.fixture(autouse=True)
def mcp_test_settings():
    """Configures SolviewSettings for every MCP test."""
    return setup_settings(
        SolviewSettings(
            service_name="test-mcp-app",
            enable_memory_profiling=False,
        )
    )


@pytest.fixture
def mcp_settings_with_memory():
    """SolviewSettings with memory profiling enabled (100 % sampling)."""
    return setup_settings(
        SolviewSettings(
            service_name="test-mcp-app",
            enable_memory_profiling=True,
            sampling_memory_profiling=1.0,
        )
    )
