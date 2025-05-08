import sys
from datetime import timedelta
from typing import Any, TextIO

import orjson
from loguru._handler import Message

from .settings import LoggingSettings

async def ecs_sink(
    message: Message, settings: LoggingSettings, stream: TextIO = sys.stdout
) -> None:
    """
    Emit log estruturado no padrão ECS (Elastic Common Schema), compatível com Elastic e Loki.

    Args:
        message (Message): Mensagem recebida pelo Loguru.
        settings (LoggingSettings): Configuração para enriquecer o log.
        stream (TextIO): Saída, padrão sys.stdout.
    """
    record = message.record

    # ---- PATCH INÍCIO: Injeta trace_id e span_id automaticamente ----
    try:
        from opentelemetry.trace import get_current_span, format_trace_id, format_span_id
        span = get_current_span()
        trace_id = None
        span_id = None
        if span and getattr(span, "get_span_context", None):
            ctx = span.get_span_context()
            if getattr(ctx, "is_valid", None) and ctx.is_valid:
                trace_id = format_trace_id(ctx.trace_id)
                span_id = format_span_id(ctx.span_id)
        record["extra"]["trace_id"] = trace_id
        record["extra"]["span_id"] = span_id
    except Exception:
        # Falha ao importar ou obter contexto: ignore silenciosamente.
        pass
    # ---- PATCH FIM ----

    log_message: dict[str, Any] = {
        "@timestamp": record["time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "event": {
            "created": record["time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "duration": int(record["elapsed"].total_seconds() * 1e9),
        },
        "labels": record["extra"],
        "level": str(record["level"].name).lower(),
        "message": record["message"],
        "log": {
            "file": {"path": record["file"].path},
            "level": str(record["level"].name).lower(),
            "logger": record["name"],
            "module": record["module"],
            "origin": {
                "file": {
                    "line": record["line"],
                    "name": record["file"].name,
                },
                "function": record["function"],
            },
        },
        "process": {
            "pid": record["process"].id,
            "name": record["process"].name,
            "thread": {
                "id": record["thread"].id,
                "name": record["thread"].name,
            },
        },
        "service": {
            "environment": settings.environment,
            "domain": settings.domain,
            "name": settings.service_name,
            "subdomain": settings.subdomain,
            "version": settings.version,
        },
    }

    exception = record.get("exception")
    if exception is not None:
        log_message["error"] = {
            "message": str(exception.value),
            "type": record["exception"].type.__name__,
        }

    json_message = orjson.dumps(log_message) + b"\n"

    # CORREÇÃO: aceita tanto sys.stdout (possui .buffer) quanto BytesIO (usado em teste)
    if hasattr(stream, "buffer"):
        stream.buffer.write(json_message)
        stream.flush()
    else:
        stream.write(json_message)
        stream.flush()