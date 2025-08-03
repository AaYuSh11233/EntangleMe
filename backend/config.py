import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Quantum computing configuration
    CLASSIQ_API_KEY = os.getenv("CLASSIQ_API_KEY", "")
    
    # Flask configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "quantum-secret-key-change-in-production")
    DEBUG = os.getenv("DEBUG", "True").lower() == "true"
    
    # Quantum messaging configuration
    MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "1000"))  # characters
    QUANTUM_SIMULATOR = os.getenv("QUANTUM_SIMULATOR", "aer_simulator")
    
    # Logging configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "logs/quantum_messaging.log")
    
    # Security configuration
    ENABLE_CORS = os.getenv("ENABLE_CORS", "True").lower() == "true"
