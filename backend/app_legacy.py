"""
Legacy entry point for the Quantum Teleportation Chat application.
This file now uses the new modular backend structure.
"""

import sys
import os

# Add the current directory to the path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app import create_app

# Create the Flask application
app = create_app()

if __name__ == '__main__':
    print("🚀 Starting Quantum Teleportation Chat Server (Legacy Mode)...")
    print("💡 Consider using 'python backend/main.py' for better startup experience")
    print("-" * 60)
    
    app.run(
        debug=app.config['DEBUG'],
        host=app.config['HOST'],
        port=app.config['PORT']
    ) 