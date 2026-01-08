import sys
import orjson
from datetime import timedelta
from typing import Any, TextIO
from loguru._handler import Message
from .settings import LoggingSettings
from .masking import DataMasker

def _mask_dict_values(data: dict, masker: DataMasker) -> dict:
    """
    Recursively mask string values in a dictionary.
    
    Args:
        data: Dictionary to mask
        masker: DataMasker instance
        
    Returns:
        Dictionary with masked values
    """
    if masker.ignore_mask:
        return data
    
    masked = {}
    for key, value in data.items():
        if isinstance(value, str):
            masked[key] = masker.mask_sensitive_data(value)
        elif isinstance(value, dict):
            masked[key] = _mask_dict_values(value, masker)
        elif isinstance(value, list):
            masked[key] = [
                masker.mask_sensitive_data(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            masked[key] = value
    return masked


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
    # Check if ignore_mask is set in the log call (via extra)
    # Se não estiver no extra, usa False (sempre mascarar por padrão)
    # Remove it from extra so it doesn't appear in labels
    ignore_mask = record["extra"].pop("ignore_mask", False)
    masker = DataMasker(ignore_mask=ignore_mask)

    # Extract trace_id and span_id from extra (added by trace_context_filter)
    trace_id = record["extra"].get("trace_id", "N/A")
    span_id = record["extra"].get("span_id", "N/A")

    log_message: dict[str, Any] = {
        "@timestamp": record["time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "event": {
            "created": record["time"].strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "duration": int(record["elapsed"].total_seconds() * 1e9),
        },
        "labels": _mask_dict_values(record["extra"], masker),
        "level": str(record["level"].name).lower(),
        "message": record["message"],  # Already masked by filter
        "trace_id": trace_id if trace_id != "N/A" else None,
        "span_id": span_id if span_id != "N/A" else None,
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
        error_message = str(exception.value)
        log_message["error"] = {
            "message": masker.mask_sensitive_data(error_message),
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