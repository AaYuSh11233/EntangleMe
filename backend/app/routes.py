from flask import Blueprint, request, jsonify
from app.quantum.teleport import teleport_text_message
import logging
import os
from datetime import datetime

# Configure logging
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/quantum_messaging.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

main = Blueprint("main", __name__)

@main.route("/teleport", methods=["POST"])
def teleport():
    """Legacy endpoint for 0/1 teleportation"""
    data = request.json
    input_state = data.get("state", "0")
    result = teleport_text_message(input_state)
    return jsonify(result)

@main.route("/send-message", methods=["POST"])
def send_message():
    """Send a text message using quantum teleportation"""
    try:
        data = request.json
        message = data.get("message", "")
        sender = data.get("sender", "User A")
        receiver = data.get("receiver", "User B")
        
        if not message:
            return jsonify({"error": "Message cannot be empty"}), 400
        
        # Log the message being sent (for demonstration - in real quantum messaging this wouldn't be stored)
        logger.info(f"QUANTUM MESSAGE SENT - Sender: {sender}, Receiver: {receiver}, Message: '{message}'")
        logger.info("NOTE: This message is NOT stored in any database - it's only teleported!")
        
        # Convert text to binary and teleport each bit
        teleportation_results = teleport_text_message(message)
        
        return jsonify({
            "status": "success",
            "message": "Message teleported successfully",
            "sender": sender,
            "receiver": receiver,
            "original_message": message,
            "teleportation_data": teleportation_results,
            "timestamp": datetime.now().isoformat(),
            "note": "Message was teleported, not stored in any database"
        })
        
    except Exception as e:
        logger.error(f"Error in send_message: {str(e)}")
        return jsonify({"error": "Failed to send message"}), 500

@main.route("/receive-message", methods=["POST"])
def receive_message():
    """Receive a teleported message"""
    try:
        data = request.json
        teleportation_data = data.get("teleportation_data", {})
        receiver = data.get("receiver", "User B")
        
        # Reconstruct message from teleportation data
        reconstructed_message = teleportation_data.get("reconstructed_message", "")
        
        logger.info(f"QUANTUM MESSAGE RECEIVED - Receiver: {receiver}, Message: '{reconstructed_message}'")
        logger.info("NOTE: This message was reconstructed from quantum teleportation, not retrieved from storage!")
        
        return jsonify({
            "status": "success",
            "message": "Message received via quantum teleportation",
            "receiver": receiver,
            "received_message": reconstructed_message,
            "timestamp": datetime.now().isoformat(),
            "note": "Message was received via quantum teleportation, not from any database"
        })
        
    except Exception as e:
        logger.error(f"Error in receive_message: {str(e)}")
        return jsonify({"error": "Failed to receive message"}), 500

@main.route("/logs", methods=["GET"])
def get_logs():
    """Get recent logs to show what's being stored vs teleported"""
    try:
        with open('logs/quantum_messaging.log', 'r') as f:
            recent_logs = f.readlines()[-50:]  # Last 50 lines
        
        return jsonify({
            "logs": recent_logs,
            "note": "These logs show what's being recorded for demonstration purposes. In real quantum messaging, even these logs wouldn't exist."
        })
    except FileNotFoundError:
        return jsonify({"logs": [], "note": "No logs found"})
