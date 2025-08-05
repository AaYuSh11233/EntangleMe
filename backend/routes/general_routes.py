"""
General routes for the Quantum Teleportation Chat application.
"""

from flask import Blueprint, jsonify, send_from_directory

# Create Blueprint for general routes
general_bp = Blueprint('general', __name__)

@general_bp.route('/')
def home():
    """Serve the main application page."""
    return send_from_directory('static', 'index.html')

@general_bp.route('/api')
def api_info():
    """Provide API information and available endpoints."""
    return jsonify({
        "message": "Quantum Qubit Teleportation Chat API",
        "version": "2.0.0",
        "description": "Send and receive individual qubits (0 or 1) via quantum teleportation",
        "endpoints": {
            "POST /api/register": "Register a new user",
            "GET /api/users": "Get list of online users",
            "POST /api/create-room": "Create a new chat room",
            "POST /api/join-room": "Join an existing room",
            "GET /api/rooms": "Get list of active rooms",
            "POST /api/send-qubit": "Send a single qubit (0 or 1) via quantum teleportation",
            "POST /api/send-qubit-sequence": "Send a sequence of qubits via quantum teleportation",
            "GET /api/messages/<room_id>": "Get messages for a room",
            "GET /health": "Health check endpoint"
        },
        "features": [
            "Individual qubit teleportation (0 or 1)",
            "Qubit sequence teleportation",
            "Real-time quantum chat rooms",
            "Anonymous user registration",
            "In-memory data storage (resets on server restart)",
            "Quantum circuit simulation with Qiskit",
            "ClassIQ API integration ready"
        ],
        "quantum_info": {
            "circuit_qubits": 3,
            "classical_bits": 2,
            "gates_used": ["X", "H", "CX", "measure"],
            "teleportation_protocol": "Bell state measurement"
        }
    })

@general_bp.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "Quantum Qubit Teleportation Chat",
        "version": "2.0.0",
        "mode": "qubit_teleportation"
    }) 