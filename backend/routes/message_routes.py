"""
Message handling routes for the Quantum Teleportation Chat application.
"""

from flask import Blueprint, request, jsonify
from ..models.data_store import data_store
from ..services.quantum_service import QuantumTeleportationService
from ..utils.helpers import generate_message_id, sanitize_data, format_timestamp

# Create Blueprint for message routes
message_bp = Blueprint('message', __name__, url_prefix='/api')

# Initialize quantum service
quantum_service = QuantumTeleportationService()

@message_bp.route('/send-qubit', methods=['POST'])
def send_qubit():
    """Send a qubit (0 or 1) via quantum teleportation."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Sanitize input data
        data = sanitize_data(data)
        user_id = data.get('user_id')
        room_id = data.get('room_id')
        qubit_value = data.get('qubit', '').strip()
        
        if not user_id or not data_store.get_user(user_id):
            return jsonify({"error": "Invalid user"}), 400
        
        if not room_id or not data_store.get_room(room_id):
            return jsonify({"error": "Invalid room"}), 400
        
        # Validate qubit value
        if qubit_value not in ["0", "1"]:
            return jsonify({"error": "Qubit value must be '0' or '1'"}), 400
        
        # Check if user is in the room
        if user_id not in data_store.get_room_participants(room_id):
            return jsonify({"error": "User not in room"}), 400
        
        # Perform quantum teleportation simulation
        teleportation_result = quantum_service.teleport_qubit(qubit_value)
        
        # Create message object
        message = {
            "id": generate_message_id(),
            "sender_id": user_id,
            "sender_username": data_store.get_user(user_id)['username'],
            "room_id": room_id,
            "original_qubit": qubit_value,
            "teleported_qubit": teleportation_result['teleported_qubit'],
            "classical_bits": teleportation_result['classical_bits'],
            "circuit_info": teleportation_result['circuit_info'],
            "timestamp": format_timestamp(),
            "success": teleportation_result['success'],
            "message_type": "qubit"
        }
        
        # Add message to room
        data_store.add_message(room_id, message)
        
        # Update user's last seen
        data_store.update_user_last_seen(user_id)
        
        return jsonify({
            "message_id": message["id"],
            "sender": data_store.get_user(user_id)['username'],
            "original_qubit": qubit_value,
            "teleported_qubit": teleportation_result['teleported_qubit'],
            "classical_bits": teleportation_result['classical_bits'],
            "circuit_info": teleportation_result['circuit_info'],
            "success": teleportation_result['success']
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@message_bp.route('/send-qubit-sequence', methods=['POST'])
def send_qubit_sequence():
    """Send a sequence of qubits via quantum teleportation."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Sanitize input data
        data = sanitize_data(data)
        user_id = data.get('user_id')
        room_id = data.get('room_id')
        qubit_sequence = data.get('qubit_sequence', [])
        
        if not user_id or not data_store.get_user(user_id):
            return jsonify({"error": "Invalid user"}), 400
        
        if not room_id or not data_store.get_room(room_id):
            return jsonify({"error": "Invalid room"}), 400
        
        # Validate qubit sequence
        if not isinstance(qubit_sequence, list) or len(qubit_sequence) == 0:
            return jsonify({"error": "Qubit sequence must be a non-empty list"}), 400
        
        for qubit in qubit_sequence:
            if qubit not in ["0", "1"]:
                return jsonify({"error": f"Invalid qubit value: {qubit}. Must be '0' or '1'"}), 400
        
        # Check if user is in the room
        if user_id not in data_store.get_room_participants(room_id):
            return jsonify({"error": "User not in room"}), 400
        
        # Perform quantum teleportation simulation
        teleportation_result = quantum_service.teleport_qubit_sequence(qubit_sequence)
        
        # Create message object
        message = {
            "id": generate_message_id(),
            "sender_id": user_id,
            "sender_username": data_store.get_user(user_id)['username'],
            "room_id": room_id,
            "original_sequence": qubit_sequence,
            "teleported_sequence": teleportation_result['teleported_sequence'],
            "individual_results": teleportation_result['individual_results'],
            "total_qubits": teleportation_result['total_qubits'],
            "successful_teleportations": teleportation_result['successful_teleportations'],
            "success_rate": teleportation_result['success_rate'],
            "timestamp": format_timestamp(),
            "message_type": "qubit_sequence"
        }
        
        # Add message to room
        data_store.add_message(room_id, message)
        
        # Update user's last seen
        data_store.update_user_last_seen(user_id)
        
        return jsonify({
            "message_id": message["id"],
            "sender": data_store.get_user(user_id)['username'],
            "original_sequence": qubit_sequence,
            "teleported_sequence": teleportation_result['teleported_sequence'],
            "total_qubits": teleportation_result['total_qubits'],
            "successful_teleportations": teleportation_result['successful_teleportations'],
            "success_rate": teleportation_result['success_rate']
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@message_bp.route('/messages/<room_id>', methods=['GET'])
def get_messages(room_id):
    """Get messages for a specific room."""
    try:
        user_id = request.args.get('user_id')
        
        if not user_id or not data_store.get_user(user_id):
            return jsonify({"error": "Invalid user"}), 400
        
        if not room_id or not data_store.get_room(room_id):
            return jsonify({"error": "Invalid room"}), 400
        
        # Check if user is in the room
        if user_id not in data_store.get_room_participants(room_id):
            return jsonify({"error": "User not in room"}), 400
        
        # Update user's last seen
        data_store.update_user_last_seen(user_id)
        
        # Return room messages
        room_messages = data_store.get_room_messages(room_id)
        
        # Get participant usernames
        participant_ids = data_store.get_room_participants(room_id)
        participant_usernames = [data_store.get_user(pid)['username'] for pid in participant_ids]
        
        return jsonify({
            "room_id": room_id,
            "messages": room_messages,
            "count": len(room_messages),
            "participants": participant_usernames
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500 