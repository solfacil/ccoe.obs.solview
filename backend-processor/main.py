#!/usr/bin/env python3
"""
🔧 Backend Processor - Service Graph Generator

Aplicação secundária para demonstrar comunicação entre serviços
e geração de service graph no Grafana via OpenTelemetry.
"""

import sys
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    import uvicorn
    from app.environment import get_settings

    settings = get_settings()

    print(f"🔧 Starting {settings.service_name} v{settings.version}")
    print(f"🌍 Environment: {settings.environment}")
    print(
        f"📊 OpenTelemetry: {'✅ Enabled' if settings.otel_enabled else '❌ Disabled'}"
    )
    print(f"🔗 Demo App URL: {settings.demo_app_url}")
    print(
        f"🚀 Service Graph: {'✅ Enabled' if settings.service_graph_enabled else '❌ Disabled'}"
    )

    uvicorn.run(
        "app.server:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.environment == "development",
    )
