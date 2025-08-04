from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from .routes import main as main_blueprint
import logging
import os
import sys

# Add parent directory to path for config import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )
    
    # Enable CORS if configured
    if app.config.get('ENABLE_CORS', True):
        CORS(app, resources={r"/*": {"origins": "*"}})
    
    # Configure logging
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logging.basicConfig(
        level=getattr(logging, app.config.get('LOG_LEVEL', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(app.config.get('LOG_FILE', 'logs/quantum_messaging.log')),
            logging.StreamHandler()
        ]
    )
    
    # Register blueprints
    app.register_blueprint(main_blueprint)
    
    # Add error handlers
    @app.errorhandler(404)
    def not_found(error):
        return {"error": "Quantum endpoint not found", "message": "Check the API documentation"}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {"error": "Quantum entanglement failed", "message": "Internal server error"}, 500
    
    @app.errorhandler(429)
    def ratelimit_handler(error):
        return {"error": "Rate limit exceeded", "message": "Too many requests, please try again later"}, 429
    
    return app
