import pytest
import logging
from fastapi import FastAPI
from starlette.testclient import TestClient
from unittest.mock import patch

def test_logger_called_for_unhandled_path(app):
    client = TestClient(app)
    with patch("solview.metrics.exporters._logger") as mock_logger:
        client.get("/notfound/path")
        # Veja se "debug" foi chamado pelo menos uma vez
        assert any(
            "is_handled_path=False" in str(call)
            for call in [c[0][0] for c in mock_logger.debug.call_args_list]
        )