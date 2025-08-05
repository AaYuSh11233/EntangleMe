"""
Utility helper functions for the Quantum Teleportation Chat application.
"""

import uuid
import hashlib
import time
from datetime import datetime
from typing import Dict, Any, Optional

def generate_room_id() -> str:
    """Generate a 32-character hashed room ID."""
    random_data = str(uuid.uuid4()) + str(time.time())
    return hashlib.md5(random_data.encode()).hexdigest()

def generate_user_id() -> str:
    """Generate a unique user ID."""
    return str(uuid.uuid4())

def generate_message_id() -> str:
    """Generate a unique message ID."""
    return str(uuid.uuid4())

def validate_username(username: str) -> tuple[bool, str]:
    """
    Validate username format and length.
    
    Args:
        username: The username to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not username or not username.strip():
        return False, "Username is required"
    
    username = username.strip()
    
    if len(username) > 20:
        return False, "Username too long (max 20 characters)"
    
    if len(username) < 1:
        return False, "Username too short (min 1 character)"
    
    return True, ""

def validate_message(message: str) -> tuple[bool, str]:
    """
    Validate message format and length.
    
    Args:
        message: The message to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not message or not message.strip():
        return False, "Message cannot be empty"
    
    if len(message) > 500:
        return False, "Message too long (max 500 characters)"
    
    return True, ""

def format_timestamp(timestamp: Optional[datetime] = None) -> str:
    """
    Format timestamp to ISO format.
    
    Args:
        timestamp: The timestamp to format (defaults to current time)
        
    Returns:
        str: ISO formatted timestamp
    """
    if timestamp is None:
        timestamp = datetime.now()
    return timestamp.isoformat()

def sanitize_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize input data by removing extra whitespace and converting to appropriate types.
    
    Args:
        data: The data dictionary to sanitize
        
    Returns:
        Dict: Sanitized data
    """
    sanitized = {}
    
    for key, value in data.items():
        if isinstance(value, str):
            sanitized[key] = value.strip()
        else:
            sanitized[key] = value
    
    return sanitized 