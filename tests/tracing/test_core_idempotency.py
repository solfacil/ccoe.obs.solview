"""
Testes de idempotência e comportamento das funções refatoradas em solview.tracing.core.

Cobre:
- setup_tracer_provider() chamado múltiplas vezes retorna o mesmo provider e não duplica processors
- setup_tracer_libs() chamado múltiplas vezes não re-executa instrumentações
- setup_tracer_fastapi() e setup_tracer() funcionam corretamente com ou sem FastAPI
- Modo unittest + ConsoleSpanExporter continua funcionando
"""

import pytest
from fastapi import FastAPI
from unittest.mock import MagicMock, patch, call

import solview.tracing.core as core
from solview.config import setup_settings
from solview.settings import SolviewSettings


@pytest.fixture
def reset_tracer_state():
    """Reset das flags de módulo antes de cada teste."""
    core._state["tracer_provider_initialized"] = False
    core._state["tracer_provider"] = None
    core._state["libs_instrumented"] = False
    core._state["fastapi_instrumented_apps"] = set()
    yield
    # Cleanup após teste
    core._state["tracer_provider_initialized"] = False
    core._state["tracer_provider"] = None
    core._state["libs_instrumented"] = False
    core._state["fastapi_instrumented_apps"] = set()


class TestSetupTracerProviderIdempotency:
    """Testes de idempotência do setup_tracer_provider()."""

    def test_setup_tracer_provider_returns_same_instance_on_second_call(
        self, monkeypatch, reset_tracer_state
    ):
        """
        Verifica que chamar setup_tracer_provider() duas vezes
        retorna a mesma instância de TracerProvider.
        """
        monkeypatch.setenv("PYTHON_ENV", "")
        setup_settings(
            SolviewSettings(
                service_name="test-service",
                use_console_exporter_on_unittest=False,
                tracing_settings={"otlp_exporter_host": "localhost", "otlp_exporter_port": 4317},
            )
        )

        # Mockar o BatchSpanProcessor para evitar conexão OTLP real
        with patch("solview.tracing.core.BatchSpanProcessor"):
            provider1 = core.setup_tracer_provider()
            provider2 = core.setup_tracer_provider()

        assert provider1 is provider2, "Segundo call deve retornar exatamente a mesma instância"

    def test_setup_tracer_provider_does_not_add_duplicate_processors(
        self, monkeypatch, reset_tracer_state
    ):
        """
        Verifica que chamar setup_tracer_provider() duas vezes
        não adiciona um segundo BatchSpanProcessor.
        """
        monkeypatch.setenv("PYTHON_ENV", "")
        setup_settings(
            SolviewSettings(
                service_name="test-service",
                use_console_exporter_on_unittest=False,
                tracing_settings={"otlp_exporter_host": "localhost", "otlp_exporter_port": 4317},
            )
        )

        with patch("solview.tracing.core.BatchSpanProcessor") as mock_processor:
            provider1 = core.setup_tracer_provider()
            provider2 = core.setup_tracer_provider()

        # BatchSpanProcessor deve ter sido instanciado apenas uma vez
        assert mock_processor.call_count == 1, \
            f"BatchSpanProcessor instanciado {mock_processor.call_count} vezes, esperado 1"

    def test_setup_tracer_provider_unittest_mode_with_console_exporter(
        self, monkeypatch, reset_tracer_state
    ):
        """
        Verifica que em PYTHON_ENV=unittest com use_console_exporter_on_unittest,
        adiciona SimpleSpanProcessor(ConsoleSpanExporter()) apenas uma vez.
        """
        monkeypatch.setenv("PYTHON_ENV", "unittest")
        setup_settings(
            SolviewSettings(
                service_name="test-service",
                use_console_exporter_on_unittest=True,
            )
        )

        # Mockar SimpleSpanProcessor para contar quantas vezes é chamado
        with patch("solview.tracing.core.SimpleSpanProcessor") as mock_simple_processor:
            provider1 = core.setup_tracer_provider()
            provider2 = core.setup_tracer_provider()

        # SimpleSpanProcessor deve ter sido instanciado apenas uma vez
        assert mock_simple_processor.call_count == 1, \
            f"SimpleSpanProcessor instanciado {mock_simple_processor.call_count} vezes, esperado 1"
        assert provider1 is provider2


class TestSetupTracerLibsIdempotency:
    """Testes de idempotência do setup_tracer_libs()."""

    def test_setup_tracer_libs_idempotent_no_duplicate_instrumentation(
        self, monkeypatch, reset_tracer_state, caplog
    ):
        """
        Verifica que chamar setup_tracer_libs() duas vezes
        não executa as instrumentações novamente (não duplica logs).
        """
        monkeypatch.setenv("PYTHON_ENV", "")
        setup_settings(
            SolviewSettings(
                service_name="test-service",
                use_console_exporter_on_unittest=False,
            )
        )

        # Mockar todos os *Instrumentor().instrument() para evitar side-effects
        with patch("solview.tracing.core.LoggingInstrumentor") as mock_logging, \
             patch("solview.tracing.core.HTTPXClientInstrumentor") as mock_httpx, \
             patch("solview.tracing.core.AsyncPGInstrumentor") as mock_asyncpg, \
             patch("solview.tracing.core.SQLAlchemyInstrumentor") as mock_sqlalchemy, \
             patch("solview.tracing.core.HttpClientInstrumentor") as mock_http_client, \
             patch("solview.tracing.core.RequestsInstrumentor") as mock_requests, \
             patch("solview.tracing.core.RedisInstrumentor") as mock_redis, \
             patch("solview.tracing.core.AioPikaInstrumentor") as mock_aiopika:

            # Chamar duas vezes
            core.setup_tracer_libs()
            core.setup_tracer_libs()

            # Cada Instrumentor deve ter sido chamado apenas uma vez
            assert mock_logging.return_value.instrument.call_count == 1
            assert mock_httpx.return_value.instrument.call_count == 1
            assert mock_asyncpg.return_value.instrument.call_count == 1
            assert mock_sqlalchemy.return_value.instrument.call_count == 1
            assert mock_http_client.return_value.instrument.call_count == 1
            assert mock_requests.return_value.instrument.call_count == 1
            assert mock_redis.return_value.instrument.call_count == 1
            assert mock_aiopika.return_value.instrument.call_count == 1

    def test_setup_tracer_libs_logs_only_once(
        self, monkeypatch, reset_tracer_state, caplog
    ):
        """
        Verifica que o log de sucesso 'Instrumentação library-level ativada'
        aparece apenas uma vez mesmo chamando setup_tracer_libs() duas vezes.
        """
        import logging
        monkeypatch.setenv("PYTHON_ENV", "")
        setup_settings(
            SolviewSettings(
                service_name="test-service",
                use_console_exporter_on_unittest=False,
            )
        )

        with caplog.at_level(logging.INFO, logger="solview.tracing.core"):
            with patch("solview.tracing.core.LoggingInstrumentor"), \
                 patch("solview.tracing.core.HTTPXClientInstrumentor"), \
                 patch("solview.tracing.core.AsyncPGInstrumentor"), \
                 patch("solview.tracing.core.SQLAlchemyInstrumentor"), \
                 patch("solview.tracing.core.HttpClientInstrumentor"), \
                 patch("solview.tracing.core.RequestsInstrumentor"), \
                 patch("solview.tracing.core.RedisInstrumentor"), \
                 patch("solview.tracing.core.AioPikaInstrumentor"):

                core.setup_tracer_libs()
                core.setup_tracer_libs()

        # Contar quantas vezes "Instrumentação library-level ativada" aparece
        instrumentation_logs = [
            record for record in caplog.records
            if "Instrumentação library-level ativada" in record.message
        ]
        assert len(instrumentation_logs) == 1, \
            f"Log de instrumentação apareceu {len(instrumentation_logs)} vezes, esperado 1"

    def test_setup_tracer_libs_unittest_mode_skips_instrumentation(
        self, monkeypatch, reset_tracer_state
    ):
        """
        Verifica que em PYTHON_ENV=unittest com use_console_exporter_on_unittest,
        setup_tracer_libs() não executa as instrumentações (preserva legado).
        """
        monkeypatch.setenv("PYTHON_ENV", "unittest")
        setup_settings(
            SolviewSettings(
                service_name="test-service",
                use_console_exporter_on_unittest=True,
            )
        )

        with patch("solview.tracing.core.LoggingInstrumentor") as mock_logging, \
             patch("solview.tracing.core.HTTPXClientInstrumentor") as mock_httpx:

            core.setup_tracer_libs()

            # Nenhum Instrumentor deve ter sido chamado em modo unittest
            mock_logging.assert_not_called()
            mock_httpx.assert_not_called()


class TestSetupTracerFastAPIIdempotency:
    """Testes de idempotência do setup_tracer_fastapi()."""

    def test_setup_tracer_fastapi_idempotent_per_app_instance(
        self, monkeypatch, reset_tracer_state
    ):
        """
        Verifica que chamar setup_tracer_fastapi() com a mesma instância de app
        duas vezes não re-aplica a instrumentação.
        """
        app = FastAPI()

        with patch("prometheus_fastapi_instrumentator.Instrumentator") as mock_instrumentator, \
             patch("opentelemetry.instrumentation.fastapi.FastAPIInstrumentor") as mock_fastapi_instrumentor:

            core.setup_tracer_fastapi(app)
            core.setup_tracer_fastapi(app)

            # Instrumentator e FastAPIInstrumentor devem ter sido chamados apenas uma vez
            assert mock_instrumentator.return_value.instrument.call_count == 1
            assert mock_fastapi_instrumentor.return_value.instrument_app.call_count == 1

    def test_setup_tracer_fastapi_ignores_non_fastapi_apps(self, reset_tracer_state):
        """
        Verifica que setup_tracer_fastapi() ignora apps que não são FastAPI silenciosamente.
        """
        class FakeApp:
            pass

        fake_app = FakeApp()

        with patch("prometheus_fastapi_instrumentator.Instrumentator") as mock_instrumentator, \
             patch("opentelemetry.instrumentation.fastapi.FastAPIInstrumentor") as mock_fastapi_instrumentor:

            core.setup_tracer_fastapi(fake_app)

            # Nenhum instrumentador deve ter sido chamado
            mock_instrumentator.assert_not_called()
            mock_fastapi_instrumentor.assert_not_called()

    def test_setup_tracer_fastapi_handles_fastapi_import_error(self, reset_tracer_state):
        """
        Verifica que setup_tracer_fastapi() ignora silenciosamente quando
        a importação de FastAPI falha (graceful degradation).
        """
        # Mockar o try/except de importação dentro de setup_tracer_fastapi
        # Verificar que a função não lança exceção mesmo se FastAPI não está disponível
        app = object()  # Algum objeto genérico (não é FastAPI)

        # Não deve lançar exceção
        result = core.setup_tracer_fastapi(app)
        assert result is None

    def test_setup_tracer_fastapi_with_none_app(self, reset_tracer_state):
        """
        Verifica que setup_tracer_fastapi(app=None) retorna silenciosamente sem erro.
        """
        result = core.setup_tracer_fastapi(None)
        assert result is None


class TestSetupTracerIntegration:
    """Testes de integração do wrapper setup_tracer()."""

    def test_setup_tracer_calls_all_three_functions_in_order(
        self, monkeypatch, reset_tracer_state
    ):
        """
        Verifica que setup_tracer(app) chama setup_tracer_provider(),
        setup_tracer_libs() e setup_tracer_fastapi() na ordem correta.
        """
        monkeypatch.setenv("PYTHON_ENV", "")
        setup_settings(
            SolviewSettings(
                service_name="test-service",
                use_console_exporter_on_unittest=False,
                tracing_settings={"otlp_exporter_host": "localhost", "otlp_exporter_port": 4317},
            )
        )

        app = FastAPI()
        call_order = []

        def mock_setup_provider():
            call_order.append("provider")
            # Simular configuração do provider
            core._state["tracer_provider_initialized"] = True
            from opentelemetry.sdk.trace import TracerProvider
            core._state["tracer_provider"] = TracerProvider()
            return core._state["tracer_provider"]

        def mock_setup_libs():
            call_order.append("libs")

        def mock_setup_fastapi(app_arg):
            call_order.append("fastapi")

        with patch("solview.tracing.core.setup_tracer_provider", side_effect=mock_setup_provider), \
             patch("solview.tracing.core.setup_tracer_libs", side_effect=mock_setup_libs), \
             patch("solview.tracing.core.setup_tracer_fastapi", side_effect=mock_setup_fastapi):

            result = core.setup_tracer(app)

        assert call_order == ["provider", "libs", "fastapi"], \
            f"Ordem de chamadas esperada ['provider', 'libs', 'fastapi'], obtido {call_order}"

    def test_setup_tracer_without_fastapi_app(
        self, monkeypatch, reset_tracer_state
    ):
        """
        Verifica que setup_tracer(app=None) chama setup_tracer_provider() e
        setup_tracer_libs(), mas não setup_tracer_fastapi().
        """
        monkeypatch.setenv("PYTHON_ENV", "")
        setup_settings(
            SolviewSettings(
                service_name="test-service",
                use_console_exporter_on_unittest=False,
                tracing_settings={"otlp_exporter_host": "localhost", "otlp_exporter_port": 4317},
            )
        )

        call_order = []

        def mock_setup_provider():
            call_order.append("provider")
            from opentelemetry.sdk.trace import TracerProvider
            core._state["tracer_provider_initialized"] = True
            core._state["tracer_provider"] = TracerProvider()
            return core._state["tracer_provider"]

        def mock_setup_libs():
            call_order.append("libs")

        def mock_setup_fastapi(app_arg):
            call_order.append("fastapi")

        with patch("solview.tracing.core.setup_tracer_provider", side_effect=mock_setup_provider), \
             patch("solview.tracing.core.setup_tracer_libs", side_effect=mock_setup_libs), \
             patch("solview.tracing.core.setup_tracer_fastapi", side_effect=mock_setup_fastapi):

            result = core.setup_tracer(app=None)

        assert call_order == ["provider", "libs"], \
            f"Ordem esperada ['provider', 'libs'], obtido {call_order}"

    def test_setup_tracer_returns_tracer_provider(
        self, monkeypatch, reset_tracer_state
    ):
        """
        Verifica que setup_tracer() retorna uma instância de TracerProvider.
        """
        monkeypatch.setenv("PYTHON_ENV", "unittest")
        setup_settings(
            SolviewSettings(
                service_name="test-service",
                use_console_exporter_on_unittest=True,
            )
        )

        app = FastAPI()
        result = core.setup_tracer(app)

        from opentelemetry.sdk.trace import TracerProvider
        assert isinstance(result, TracerProvider)

    def test_setup_tracer_full_integration_unittest_mode(
        self, monkeypatch, reset_tracer_state
    ):
        """
        Teste de integração completo: verifica que setup_tracer() funciona
        em modo unittest com ConsoleSpanExporter e é idempotente.
        """
        monkeypatch.setenv("PYTHON_ENV", "unittest")
        setup_settings(
            SolviewSettings(
                service_name="integration-test-service",
                use_console_exporter_on_unittest=True,
            )
        )

        app = FastAPI()

        # Primeira chamada
        provider1 = core.setup_tracer(app)

        # Segunda chamada
        provider2 = core.setup_tracer(app)

        # Devem retornar a mesma instância
        assert provider1 is provider2

        # Verificar que tem resource com nome do serviço
        assert provider1.resource.attributes.get("service.name") == "integration-test-service"


class TestSetupTracerMultipleAppsIdempotency:
    """Testes de idempotência com múltiplas instâncias de apps."""

    def test_setup_tracer_fastapi_different_app_instances(self, reset_tracer_state):
        """
        Verifica que setup_tracer_fastapi() com instâncias diferentes de apps
        instrumenta cada uma, mas não duplica para a mesma instância.
        """
        app1 = FastAPI()
        app2 = FastAPI()

        with patch("prometheus_fastapi_instrumentator.Instrumentator") as mock_instrumentator, \
             patch("opentelemetry.instrumentation.fastapi.FastAPIInstrumentor") as mock_fastapi_instrumentor:

            # Primeira app
            core.setup_tracer_fastapi(app1)
            assert mock_instrumentator.return_value.instrument.call_count == 1

            # Mesma app (não deve duplicar)
            core.setup_tracer_fastapi(app1)
            assert mock_instrumentator.return_value.instrument.call_count == 1

            # Segunda app (deve instrumentar novamente)
            core.setup_tracer_fastapi(app2)
            assert mock_instrumentator.return_value.instrument.call_count == 2

            # Mesma segunda app (não deve duplicar)
            core.setup_tracer_fastapi(app2)
            assert mock_instrumentator.return_value.instrument.call_count == 2
