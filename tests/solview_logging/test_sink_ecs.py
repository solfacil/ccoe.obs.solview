import io
import orjson
import asyncio
from solview.solview_logging.settings import LoggingSettings

class DummyRecord(dict):
    def __getitem__(self, key):
        from datetime import datetime, timedelta
        if key == "time":
            return datetime(2024, 6, 1, 12, 0, 0)
        if key == "elapsed":
            return timedelta(seconds=5)
        if key == "extra":
            return {"foo": "bar"}
        if key == "level":
            class Level: name = "INFO"
            return Level()
        if key == "message":
            return "Test log"
        if key == "file":
            class File: path = "/tmp/file.py"; name="file.py"
            return File()
        if key == "name":
            return "mylogger"
        if key == "module":
            return "mod"
        if key == "line":
            return 99
        if key == "function":
            return "myfunc"
        if key == "process":
            class Proc:
                id = 123
                name = "proc"
            return Proc()
        if key == "thread":
            class Th:
                id = 999
                name = "Thread"
            return Th()
        if key == "exception":
            return None
        return super().__getitem__(key)

class DummyMessage:
    def __init__(self):
        self.record = DummyRecord()

def test_ecs_sink_basic():
    from solview.solview_logging.sinks import ecs_sink
    stream = io.BytesIO()
    message = DummyMessage()
    settings = LoggingSettings(environment="prod", service_name="svc", domain="dm", subdomain="sd", version="2.0")
    async def fake_sink_run():
        await ecs_sink(message, settings, stream=stream)
    asyncio.run(fake_sink_run())
    val = stream.getvalue()
    data = orjson.loads(val)
    assert data["@timestamp"].startswith("2024-06-01")
    assert data["message"] == "Test log"
    assert data["service"]["name"] == "svc"
    assert data["service"]["environment"] == "prod"
    assert data["labels"]["foo"] == "bar"