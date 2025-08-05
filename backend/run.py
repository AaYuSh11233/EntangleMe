"""
Main entry point for the Quantum Teleportation Chat application.
This file serves as the primary way to run the application.
"""

import os
import sys

# Add the parent directory to the path so we can import the backend package
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app

def main():
    """Main function to run the application."""
    # Get configuration from environment
    config_name = os.environ.get('FLASK_ENV', 'development')
    
    # Create and run the application
    app = create_app(config_name)
    
    print("🚀 Starting Quantum Teleportation Chat Server...")
    print("🔬 Qubit Teleportation Mode: Send 0 or 1 qubits")
    print(f"🌍 Environment: {config_name}")
    print(f"📍 Host: {app.config['HOST']}")
    print(f"🔌 Port: {app.config['PORT']}")
    print(f"🐛 Debug: {app.config['DEBUG']}")
    print(f"📚 API Documentation: http://{app.config['HOST']}:{app.config['PORT']}/api")
    print(f"❤️ Health Check: http://{app.config['HOST']}:{app.config['PORT']}/health")
    print("=" * 60)
    
    app.run(
        debug=app.config['DEBUG'],
        host=app.config['HOST'],
        port=app.config['PORT']
    )

if __name__ == '__main__':
    main() 