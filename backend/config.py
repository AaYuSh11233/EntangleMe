import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Quantum computing configuration
    CLASSIQ_API_KEY = os.getenv("CLASSIQ_API_KEY", "")
    
    # Flask configuration
    SECRET_KEY = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY environment variable must be set")
    
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Quantum messaging configuration
    MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "1000"))  # characters
    QUANTUM_SIMULATOR = os.getenv("QUANTUM_SIMULATOR", "aer_simulator")
    
    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/quantum_messaging.log")
    
    # Security configuration
    ENABLE_CORS = os.getenv("ENABLE_CORS", "True").lower() == "true"
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    
    # API configuration
    API_RATE_LIMIT = os.getenv("API_RATE_LIMIT", "100")  # requests per minute
