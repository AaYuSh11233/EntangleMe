from app import create_app
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = create_app()

if __name__ == "__main__":
    logger.info("🚀 Starting EntangleMe Quantum Messaging Server")
    logger.info("📡 Server will be available at http://localhost:5000")
    logger.info("🔐 Quantum teleportation endpoints:")
    logger.info("   GET  /health - Health check and monitoring")
    logger.info("   POST /teleport - Legacy 0/1 teleportation (30/min)")
    logger.info("   POST /send-message - Send text messages via quantum teleportation (20/min)")
    logger.info("   POST /receive-message - Receive teleported messages (30/min)")
    logger.info("   GET  /logs - View quantum messaging logs (10/min)")
    logger.info("🔒 Security features: Input sanitization, rate limiting, secure logging")
    
    try:
        app.run(debug=True, host="0.0.0.0", port=5000)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        exit(1)
