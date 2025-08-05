"""
Room management routes for the Quantum Teleportation Chat application.
"""

from flask import Blueprint, request, jsonify
from ..models.data_store import data_store
from ..utils.helpers import generate_room_id, sanitize_data

# Create Blueprint for room routes
room_bp = Blueprint('room', __name__, url_prefix='/api')

@room_bp.route('/create-room', methods=['POST'])
def create_room():
    """Create a new chat room."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Sanitize input data
        data = sanitize_data(data)
        user_id = data.get('user_id')
        
        if not user_id or not data_store.get_user(user_id):
            return jsonify({"error": "Invalid user"}), 400
        
        # Generate room ID
        room_id = generate_room_id()
        
        # Create room
        room_data = data_store.create_room(room_id, user_id)
        
        # Add user to room
        data_store.set_user_room(user_id, room_id)
        
        # Get participant usernames
        participant_usernames = [data_store.get_user(user_id)['username']]
        
        return jsonify({
            "room_id": room_id,
            "message": "Room created successfully",
            "participants": participant_usernames
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@room_bp.route('/join-room', methods=['POST'])
def join_room():
    """Join an existing chat room."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Sanitize input data
        data = sanitize_data(data)
        user_id = data.get('user_id')
        room_id = data.get('room_id')
        
        if not user_id or not data_store.get_user(user_id):
            return jsonify({"error": "Invalid user"}), 400
        
        if not room_id or not data_store.get_room(room_id):
            return jsonify({"error": "Invalid room ID"}), 400
        
        # Add user to room
        data_store.add_user_to_room(room_id, user_id)
        
        # Update user's current room
        data_store.set_user_room(user_id, room_id)
        
        # Get participant usernames
        participant_ids = data_store.get_room_participants(room_id)
        participant_usernames = [data_store.get_user(pid)['username'] for pid in participant_ids]
        
        return jsonify({
            "room_id": room_id,
            "message": "Joined room successfully",
            "participants": participant_usernames
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@room_bp.route('/rooms', methods=['GET'])
def get_rooms():
    """Get list of active rooms."""
    try:
        room_list = []
        for room_data in data_store.get_all_rooms():
            participant_ids = room_data['participants']
            participant_usernames = [data_store.get_user(pid)['username'] for pid in participant_ids]
            
            room_list.append({
                "room_id": room_data['id'],
                "created_by": room_data['created_by'],
                "created_at": room_data['created_at'],
                "participants": participant_usernames,
                "message_count": len(room_data['messages'])
            })
        
        return jsonify({
            "rooms": room_list,
            "count": len(room_list)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500 