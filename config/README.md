# Config files

This folder contains environment templates for Solview.

## How to use

1. Copy `config/solview.env.example` to the root as `.env` (or to your app folder).
2. Review each variable and adjust values for your environment.
3. Ensure your process manager/container loads the `.env` before application startup.

```bash
cp config/solview.env.example .env
```

## Variable reference

- `SOLVIEW_LOG_LEVEL`: Logger level (DEBUG/INFO/WARNING/ERROR).
- `SOLVIEW_ENVIRONMENT`: Deployment environment name. Use `dev` for development and staging, `prd`/`prod`/`production` for production. Internally Solview exposes `environment_effective` which normalizes values to only `dev` or `prd`.
- `SOLVIEW_SERVICE_NAME`: Technical service name used in logs/metrics/traces.
- `SOLVIEW_DOMAIN` / `SOLVIEW_SUBDOMAIN`: Optional business metadata for logs.
- `SOLVIEW_VERSION`: Version tag of your application/library.
- `OTEL_SERVICE_NAMESPACE`: OTEL service namespace (team/domain) for Tempo/Grafana grouping.
- `SOLVIEW_ENABLE_DATA_MASKING`: Enables advanced masking in logs.
- `SOLVIEW_LOG_RETENTION_DAYS`: Informational log retention policy (days).
- `OTEL_EXPORTER_OTLP_PROTOCOL`: OTLP protocol (grpc/http).
- `OTEL_EXPORTER_OTLP_ENDPOINT`: Hostname of OTLP endpoint (Tempo/Collector).
- `OTEL_EXPORTER_OTLP_PORT`: Port of OTLP endpoint (4317 grpc / 4318 http).
- `OTEL_EXPORTER_OTLP_HTTP_ENCRYPTED`: Use HTTPS for HTTP exporter.
- `OTEL_EXPORTER_OTLP_AUTH_TOKEN`: Optional auth token for managed backends.
- `OTEL_SQLALCHEMY_ENABLE_COMMENTER`: Adds `traceparent` as SQL comment.
- `OTEL_TRACES_SAMPLER`: Sampler strategy (always_on/always_off/parentbased_traceidratio).
- `OTEL_TRACES_SAMPLER_ARG`: Ratio for TraceIdRatioBased (0.0..1.0).
- `SOLVIEW_METRICS_ENABLED`: Enables Prometheus middleware.
- `SOLVIEW_METRICS_PORT`: Port for the metrics endpoint exposure.
- `SOLVIEW_METRICS_PATH`: Path for metrics endpoint.
- `KUBERNETES_NAMESPACE`/`KUBERNETES_NODE_NAME`: Optional runtime metadata in clusters.
- `PYTHON_ENV`: When set to `unittest`, enables a console exporter safe for pytest.


