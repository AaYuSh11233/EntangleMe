"""
User management routes for the Quantum Teleportation Chat application.
"""

from flask import Blueprint, request, jsonify
from ..models.data_store import data_store
from ..utils.helpers import generate_user_id, validate_username, sanitize_data

# Create Blueprint for user routes
user_bp = Blueprint('user', __name__, url_prefix='/api')

@user_bp.route('/register', methods=['POST'])
def register_user():
    """Register a new user for quantum messaging."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Sanitize input data
        data = sanitize_data(data)
        username = data.get('username', '')
        
        # Validate username
        is_valid, error_message = validate_username(username)
        if not is_valid:
            return jsonify({"error": error_message}), 400
        
        # Create new user
        user_id = generate_user_id()
        user_data = data_store.add_user(user_id, username)
        
        return jsonify({
            "user_id": user_id,
            "username": username,
            "message": "User registered successfully"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_bp.route('/users', methods=['GET'])
def get_users():
    """Get list of online users."""
    try:
        user_list = []
        for user_data in data_store.get_all_users():
            user_list.append({
                "user_id": user_data['user_id'],
                "username": user_data['username'],
                "last_seen": user_data['last_seen'],
                "current_room": user_data['current_room']
            })
        
        return jsonify({
            "users": user_list,
            "count": len(user_list)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500 