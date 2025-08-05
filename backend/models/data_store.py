"""
In-memory data store for the Quantum Teleportation Chat application.
This provides a simple storage solution that will be lost on refresh as requested.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from ..utils.helpers import format_timestamp

class DataStore:
    """In-memory data store for managing users, rooms, and messages."""
    
    def __init__(self):
        """Initialize the data store with empty collections."""
        self.users: Dict[str, Dict[str, Any]] = {}
        self.rooms: Dict[str, Dict[str, Any]] = {}
        self.messages: Dict[str, List[Dict[str, Any]]] = {}
    
    # User Management
    def add_user(self, user_id: str, username: str) -> Dict[str, Any]:
        """
        Add a new user to the data store.
        
        Args:
            user_id: Unique user identifier
            username: User's display name
            
        Returns:
            Dictionary containing user data
        """
        user_data = {
            'user_id': user_id,
            'username': username,
            'created_at': format_timestamp(),
            'last_seen': format_timestamp(),
            'current_room': None
        }
        self.users[user_id] = user_data
        return user_data
    
    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user data by user ID.
        
        Args:
            user_id: User identifier
            
        Returns:
            User data dictionary or None if not found
        """
        return self.users.get(user_id)
    
    def update_user_last_seen(self, user_id: str) -> bool:
        """
        Update user's last seen timestamp.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if user exists and was updated, False otherwise
        """
        if user_id in self.users:
            self.users[user_id]['last_seen'] = format_timestamp()
            return True
        return False
    
    def set_user_room(self, user_id: str, room_id: Optional[str]) -> bool:
        """
        Set user's current room.
        
        Args:
            user_id: User identifier
            room_id: Room identifier or None to leave room
            
        Returns:
            True if user exists and was updated, False otherwise
        """
        if user_id in self.users:
            self.users[user_id]['current_room'] = room_id
            return True
        return False
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """
        Get all users in the system.
        
        Returns:
            List of user data dictionaries
        """
        return list(self.users.values())
    
    # Room Management
    def create_room(self, room_id: str, created_by: str) -> Dict[str, Any]:
        """
        Create a new chat room.
        
        Args:
            room_id: Unique room identifier
            created_by: User ID of room creator
            
        Returns:
            Dictionary containing room data
        """
        room_data = {
            'id': room_id,
            'created_by': created_by,
            'created_at': format_timestamp(),
            'participants': [created_by],
            'messages': []
        }
        self.rooms[room_id] = room_data
        return room_data
    
    def get_room(self, room_id: str) -> Optional[Dict[str, Any]]:
        """
        Get room data by room ID.
        
        Args:
            room_id: Room identifier
            
        Returns:
            Room data dictionary or None if not found
        """
        return self.rooms.get(room_id)
    
    def add_user_to_room(self, room_id: str, user_id: str) -> bool:
        """
        Add a user to a room.
        
        Args:
            room_id: Room identifier
            user_id: User identifier
            
        Returns:
            True if room exists and user was added, False otherwise
        """
        if room_id in self.rooms and user_id not in self.rooms[room_id]['participants']:
            self.rooms[room_id]['participants'].append(user_id)
            return True
        return False
    
    def remove_user_from_room(self, room_id: str, user_id: str) -> bool:
        """
        Remove a user from a room.
        
        Args:
            room_id: Room identifier
            user_id: User identifier
            
        Returns:
            True if user was removed, False otherwise
        """
        if room_id in self.rooms and user_id in self.rooms[room_id]['participants']:
            self.rooms[room_id]['participants'].remove(user_id)
            return True
        return False
    
    def get_room_participants(self, room_id: str) -> List[str]:
        """
        Get list of participant user IDs in a room.
        
        Args:
            room_id: Room identifier
            
        Returns:
            List of user IDs
        """
        if room_id in self.rooms:
            return self.rooms[room_id]['participants']
        return []
    
    def get_all_rooms(self) -> List[Dict[str, Any]]:
        """
        Get all rooms in the system.
        
        Returns:
            List of room data dictionaries
        """
        return list(self.rooms.values())
    
    # Message Management
    def add_message(self, room_id: str, message_data: Dict[str, Any]) -> bool:
        """
        Add a message to a room.
        
        Args:
            room_id: Room identifier
            message_data: Message data dictionary
            
        Returns:
            True if room exists and message was added, False otherwise
        """
        if room_id in self.rooms:
            self.rooms[room_id]['messages'].append(message_data)
            return True
        return False
    
    def get_room_messages(self, room_id: str) -> List[Dict[str, Any]]:
        """
        Get all messages in a room.
        
        Args:
            room_id: Room identifier
            
        Returns:
            List of message data dictionaries
        """
        if room_id in self.rooms:
            return self.rooms[room_id]['messages']
        return []
    
    def get_message_count(self, room_id: str) -> int:
        """
        Get the number of messages in a room.
        
        Args:
            room_id: Room identifier
            
        Returns:
            Number of messages
        """
        if room_id in self.rooms:
            return len(self.rooms[room_id]['messages'])
        return 0

# Global data store instance
data_store = DataStore() 