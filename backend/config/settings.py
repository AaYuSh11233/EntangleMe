"""
Configuration settings for the Quantum Teleportation Chat application.
"""

import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'quantum-teleportation-secret-key-2024'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Server Configuration
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 5000))
    
    # CORS Configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*').split(',')
    
    # Application Settings
    MAX_MESSAGE_LENGTH = 500
    MAX_USERNAME_LENGTH = 20
    MAX_ROOM_PARTICIPANTS = 50
    
    # Session Configuration
    SESSION_TIMEOUT = timedelta(hours=24)
    
    # Quantum Simulation Settings
    QUANTUM_SHOTS = 1
    QUANTUM_BACKEND = 'qasm_simulator'
    
    # ClassIQ API Configuration (for future use)
    CLASSIQ_API_KEY = os.environ.get('CLASSIQ_API_KEY')
    CLASSIQ_BASE_URL = "https://api.classiq.io"

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 