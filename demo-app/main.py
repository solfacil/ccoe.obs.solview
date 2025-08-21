#!/usr/bin/env python3
"""
🚀 Solview Demo Application - Main Entry Point

Entry point principal para a aplicação demo estruturada.
Configura observabilidade e inicia o servidor FastAPI.
"""

import sys
from pathlib import Path

# Adicionar src ao Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    import uvicorn
    from app.server import app
    from app.environment import get_settings
    
    settings = get_settings()
    
    print(f"🚀 Starting {settings.service_name} v{settings.version}")
    print(f"🌍 Environment: {settings.environment}")
    print(f"📊 OpenTelemetry: {'✅ Enabled' if settings.otel_enabled else '❌ Disabled'}")
    print(f"🔗 Service Graph: {'✅ Enabled' if settings.service_graph_enabled else '❌ Disabled'}")
    
    uvicorn.run(
        "app.server:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development"
    )
