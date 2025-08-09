from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import os

from app.core.config import settings
from app.api import quantum, chat
from app.database.session import engine
from app.models.database import Base

# Create database tables
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    
    # Reset database in production if RESET_DB environment variable is set
    if os.getenv("RESET_DB", "false").lower() == "true" or os.getenv("ENVIRONMENT") == "production":
        print(" Resetting database for production...")
        try:
            # Drop all tables and recreate them
            Base.metadata.drop_all(bind=engine)
            Base.metadata.create_all(bind=engine)
            print("✅ Database reset completed")
        except Exception as e:
            print(f"⚠️ Database reset failed: {e}")
    
    yield
    # Shutdown
    pass

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Quantum Teleportation Chat API - Secure messaging using quantum principles",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(quantum.router, prefix=settings.API_V1_STR)
app.include_router(chat.router, prefix=settings.API_V1_STR)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to EntangleME - Quantum Teleportation Chat API",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc"
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "EntangleME Backend",
        "version": settings.VERSION
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
