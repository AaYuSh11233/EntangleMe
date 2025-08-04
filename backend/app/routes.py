from flask import Blueprint, request, jsonify
from flask_limiter import limiter
from app.quantum.teleport import teleport_text_message
import logging
import os
import re
from datetime import datetime

logger = logging.getLogger(__name__)

main = Blueprint("main", __name__)

def sanitize_input(text: str, max_length: int = 1000) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', '', text)
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()

@main.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        "status": "healthy",
        "service": "EntangleMe Quantum Messaging",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    })

@main.route("/teleport", methods=["POST"])
@limiter.limit("30 per minute")
def teleport():
    """Legacy endpoint for 0/1 teleportation"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        input_state = data.get("state", "0")
        
        # Validate input state
        if input_state not in ["0", "1"]:
            return jsonify({"error": "State must be '0' or '1'"}), 400
            
        result = teleport_text_message(input_state)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in teleport: {str(e)}")
        return jsonify({"error": "Teleportation failed"}), 500

@main.route("/send-message", methods=["POST"])
@limiter.limit("20 per minute")
def send_message():
    """Send a text message using quantum teleportation"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        # Sanitize all inputs
        message = sanitize_input(data.get("message", ""))
        sender = sanitize_input(data.get("sender", "User A"), 50)
        receiver = sanitize_input(data.get("receiver", "User B"), 50)
        
        if not message:
            return jsonify({"error": "Message cannot be empty"}), 400
        
        if len(message) > 1000:  # Use config value
            return jsonify({"error": "Message too long"}), 400
        
        # SECURE LOGGING - Only log metadata, not content
        logger.info(f"QUANTUM MESSAGE SENT - Sender: {sender}, Receiver: {receiver}, Length: {len(message)} chars")
        logger.info("SECURITY: Message content NOT logged - only teleported!")
        
        # Convert text to binary and teleport each bit
        teleportation_results = teleport_text_message(message)
        
        return jsonify({
            "status": "success",
            "message": "Message teleported successfully",
            "sender": sender,
            "receiver": receiver,
            "message_length": len(message),
            "teleportation_data": teleportation_results,
            "timestamp": datetime.now().isoformat(),
            "security_note": "Message content not stored or logged - only teleported"
        })
        
    except ValueError as e:
        logger.error(f"Validation error in send_message: {str(e)}")
        return jsonify({"error": "Invalid input data"}), 400
    except Exception as e:
        logger.error(f"Unexpected error in send_message: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@main.route("/receive-message", methods=["POST"])
@limiter.limit("30 per minute")
def receive_message():
    """Receive a teleported message"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        teleportation_data = data.get("teleportation_data", {})
        receiver = sanitize_input(data.get("receiver", "User B"), 50)
        
        # Reconstruct message from teleportation data
        reconstructed_message = teleportation_data.get("reconstructed_message", "")
        
        # SECURE LOGGING - Only log metadata
        logger.info(f"QUANTUM MESSAGE RECEIVED - Receiver: {receiver}, Length: {len(reconstructed_message)} chars")
        logger.info("SECURITY: Message content NOT logged - only reconstructed from teleportation!")
        
        return jsonify({
            "status": "success",
            "message": "Message received via quantum teleportation",
            "receiver": receiver,
            "received_message": reconstructed_message,  # Only returned to receiver
            "message_length": len(reconstructed_message),
            "timestamp": datetime.now().isoformat(),
            "security_note": "Message reconstructed from quantum teleportation, not from storage"
        })
        
    except Exception as e:
        logger.error(f"Error in receive_message: {str(e)}")
        return jsonify({"error": "Failed to receive message"}), 500

@main.route("/logs", methods=["GET"])
@limiter.limit("10 per minute")
def get_logs():
    """Get recent logs to show what's being recorded vs teleported"""
    try:
        with open('logs/quantum_messaging.log', 'r') as f:
            recent_logs = f.readlines()[-50:]  # Last 50 lines
        
        return jsonify({
            "logs": recent_logs,
            "security_note": "Logs contain only metadata (length) - NO message content is logged for security"
        })
    except FileNotFoundError:
        return jsonify({"logs": [], "security_note": "No logs found"})
