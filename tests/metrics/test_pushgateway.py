"""Tests for push_metrics_to_gateway, delete_metrics_from_gateway, and script_metrics_context."""

import pytest
from unittest.mock import patch, call

from solview.metrics.pushgateway import (
    push_metrics_to_gateway,
    delete_metrics_from_gateway,
    script_metrics_context,
)


class TestPushMetricsToGateway:
    def test_returns_true_on_success(self):
        with patch("solview.metrics.pushgateway._push_to_gateway"):
            result = push_metrics_to_gateway("http://gw:9091", "test-job")
        assert result is True

    def test_returns_false_on_exception(self):
        with patch(
            "solview.metrics.pushgateway._push_to_gateway",
            side_effect=ConnectionError("unreachable"),
        ):
            result = push_metrics_to_gateway("http://gw:9091", "test-job")
        assert result is False

    def test_does_not_raise_on_exception(self):
        with patch(
            "solview.metrics.pushgateway._push_to_gateway",
            side_effect=Exception("boom"),
        ):
            push_metrics_to_gateway("http://gw:9091", "test-job")

    def test_passes_job_name_and_grouping_key(self):
        with patch("solview.metrics.pushgateway._push_to_gateway") as mock:
            push_metrics_to_gateway(
                "http://gw:9091", "my-job", grouping_key={"instance": "pod-1"}
            )
        _, kwargs = mock.call_args
        assert kwargs["job"] == "my-job"
        assert kwargs["grouping_key"] == {"instance": "pod-1"}

    def test_none_grouping_key_becomes_empty_dict(self):
        with patch("solview.metrics.pushgateway._push_to_gateway") as mock:
            push_metrics_to_gateway("http://gw:9091", "my-job", grouping_key=None)
        _, kwargs = mock.call_args
        assert kwargs["grouping_key"] == {}

    def test_passes_gateway_url(self):
        with patch("solview.metrics.pushgateway._push_to_gateway") as mock:
            push_metrics_to_gateway("http://gw:9091", "my-job")
        _, kwargs = mock.call_args
        assert kwargs["gateway"] == "http://gw:9091"

    def test_passes_timeout(self):
        with patch("solview.metrics.pushgateway._push_to_gateway") as mock:
            push_metrics_to_gateway("http://gw:9091", "my-job", timeout=10)
        _, kwargs = mock.call_args
        assert kwargs["timeout"] == 10


class TestDeleteMetricsFromGateway:
    def test_returns_true_on_success(self):
        with patch("solview.metrics.pushgateway._delete_from_gateway"):
            result = delete_metrics_from_gateway("http://gw:9091", "test-job")
        assert result is True

    def test_returns_false_on_exception(self):
        with patch(
            "solview.metrics.pushgateway._delete_from_gateway",
            side_effect=Exception("fail"),
        ):
            result = delete_metrics_from_gateway("http://gw:9091", "test-job")
        assert result is False

    def test_does_not_raise_on_exception(self):
        with patch(
            "solview.metrics.pushgateway._delete_from_gateway",
            side_effect=Exception("boom"),
        ):
            delete_metrics_from_gateway("http://gw:9091", "test-job")

    def test_none_grouping_key_becomes_empty_dict(self):
        with patch("solview.metrics.pushgateway._delete_from_gateway") as mock:
            delete_metrics_from_gateway("http://gw:9091", "my-job", grouping_key=None)
        _, kwargs = mock.call_args
        assert kwargs["grouping_key"] == {}


class TestScriptMetricsContext:
    def test_pushes_on_clean_exit(self):
        with patch(
            "solview.metrics.pushgateway.push_metrics_to_gateway"
        ) as mock_push:
            with script_metrics_context("http://gw:9091", "ctx-job"):
                pass
        mock_push.assert_called_once()
        _, kwargs = mock_push.call_args
        assert kwargs["gateway_url"] == "http://gw:9091"
        assert kwargs["job_name"] == "ctx-job"

    def test_pushes_on_exception_exit(self):
        with patch(
            "solview.metrics.pushgateway.push_metrics_to_gateway"
        ) as mock_push:
            with pytest.raises(RuntimeError):
                with script_metrics_context("http://gw:9091", "ctx-job"):
                    raise RuntimeError("script failed")
        mock_push.assert_called_once()

    def test_exception_is_not_suppressed(self):
        with patch("solview.metrics.pushgateway.push_metrics_to_gateway"):
            with pytest.raises(ValueError, match="expected"):
                with script_metrics_context("http://gw:9091", "ctx-job"):
                    raise ValueError("expected")

    def test_delete_on_exit_calls_delete(self):
        with patch("solview.metrics.pushgateway.push_metrics_to_gateway"):
            with patch(
                "solview.metrics.pushgateway.delete_metrics_from_gateway"
            ) as mock_del:
                with script_metrics_context(
                    "http://gw:9091", "ctx-job", delete_on_exit=True
                ):
                    pass
        mock_del.assert_called_once()

    def test_no_delete_by_default(self):
        with patch("solview.metrics.pushgateway.push_metrics_to_gateway"):
            with patch(
                "solview.metrics.pushgateway.delete_metrics_from_gateway"
            ) as mock_del:
                with script_metrics_context("http://gw:9091", "ctx-job"):
                    pass
        mock_del.assert_not_called()

    def test_passes_grouping_key_to_push(self):
        with patch(
            "solview.metrics.pushgateway.push_metrics_to_gateway"
        ) as mock_push:
            with script_metrics_context(
                "http://gw:9091",
                "ctx-job",
                grouping_key={"instance": "pod-1"},
            ):
                pass
        _, kwargs = mock_push.call_args
        assert kwargs["grouping_key"] == {"instance": "pod-1"}
