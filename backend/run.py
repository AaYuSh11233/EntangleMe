#!/usr/bin/env python3
"""
EntangleME Backend - Quantum Teleportation Chat API
Run script for development and production
"""

import uvicorn
from app.main import app
from app.core.config import settings

if __name__ == "__main__":
    print("🚀 Starting EntangleME Backend...")
    print(f"📡 API will be available at: http://{settings.HOST}:{settings.PORT}")
    print(f"📚 API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    print(f"🔬 Quantum Simulator: {settings.QUANTUM_SIMULATOR}")
    print("=" * 50)
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
