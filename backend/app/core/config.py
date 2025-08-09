from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # API Configuration
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "EntangleME - Quantum Teleportation Chat"
    VERSION: str = "1.0.0"
    
    # Server Configuration
    HOST: str = "localhost"
    PORT: int = 8000
    DEBUG: bool = True
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./entangleme.db"
    
    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379"
    
    # JWT Configuration
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Quantum Configuration
    QUANTUM_SIMULATOR: str = "qasm_simulator"
    QUANTUM_SHOTS: int = 1
    
    class Config:
        env_file = ".env"

settings = Settings()
