from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from app.models.database import User, Room, RoomParticipant, Message
from app.schemas.chat import UserCreate, RoomCreate, MessageCreate

class ChatService:
    def __init__(self, db: Session):
        self.db = db
    
    # User management
    def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        db_user = User(
            username=user_data.username,
            email=user_data.email
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def update_user_status(self, user_id: str, is_online: bool) -> Optional[User]:
        """Update user online status"""
        user = self.get_user(user_id)
        if user:
            user.is_online = is_online
            user.last_seen = datetime.utcnow()
            self.db.commit()
            self.db.refresh(user)
        return user
    
    def get_online_users(self) -> List[User]:
        """Get all online users"""
        return self.db.query(User).filter(User.is_online == True).all()
    
    # Room management
    def create_room(self, room_data: RoomCreate, created_by: str) -> Room:
        """Create a new chat room"""
        db_room = Room(
            name=room_data.name,
            created_by=created_by
        )
        self.db.add(db_room)
        self.db.commit()
        self.db.refresh(db_room)
        
        # Add creator to room
        self.add_user_to_room(db_room.id, created_by)
        
        # Add other participants
        for user_id in room_data.participant_ids:
            if user_id != created_by:
                self.add_user_to_room(db_room.id, user_id)
        
        return db_room
    
    def get_room(self, room_id: str) -> Optional[Room]:
        """Get room by ID"""
        return self.db.query(Room).filter(Room.id == room_id).first()
    
    def get_user_rooms(self, user_id: str) -> List[Room]:
        """Get all rooms for a user"""
        return self.db.query(Room).join(RoomParticipant).filter(
            RoomParticipant.user_id == user_id
        ).all()
    
    def get_all_rooms(self) -> List[Room]:
        """Get all rooms"""
        return self.db.query(Room).all()
    
    def add_user_to_room(self, room_id: str, user_id: str) -> bool:
        """Add user to room"""
        # Check if user is already in room
        existing = self.db.query(RoomParticipant).filter(
            and_(RoomParticipant.room_id == room_id, RoomParticipant.user_id == user_id)
        ).first()
        
        if existing:
            return False
        
        participant = RoomParticipant(room_id=room_id, user_id=user_id)
        self.db.add(participant)
        self.db.commit()
        return True
    
    def remove_user_from_room(self, room_id: str, user_id: str) -> bool:
        """Remove user from room"""
        participant = self.db.query(RoomParticipant).filter(
            and_(RoomParticipant.room_id == room_id, RoomParticipant.user_id == user_id)
        ).first()
        
        if participant:
            self.db.delete(participant)
            self.db.commit()
            return True
        return False
    
    def get_room_participants(self, room_id: str) -> List[User]:
        """Get all participants in a room"""
        return self.db.query(User).join(RoomParticipant).filter(
            RoomParticipant.room_id == room_id
        ).all()
    
    # Message management
    def create_message(self, message_data: MessageCreate, sender_id: str) -> Message:
        """Create a new message"""
        db_message = Message(
            room_id=message_data.room_id,
            sender_id=sender_id,
            content=message_data.content,
            quantum_state=message_data.quantum_state
        )
        self.db.add(db_message)
        self.db.commit()
        self.db.refresh(db_message)
        
        # Update room last activity
        room = self.get_room(message_data.room_id)
        if room:
            room.last_activity = datetime.utcnow()
            self.db.commit()
        
        return db_message
    
    def get_room_messages(self, room_id: str, limit: int = 50, offset: int = 0) -> List[Message]:
        """Get messages for a room"""
        return self.db.query(Message).filter(
            Message.room_id == room_id
        ).order_by(desc(Message.created_at)).offset(offset).limit(limit).all()
    
    def update_message_status(self, message_id: str, status: str, teleportation_result: Optional[Dict] = None) -> Optional[Message]:
        """Update message status (e.g., after quantum teleportation)"""
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if message:
            message.status = status
            if teleportation_result:
                message.teleportation_result = teleportation_result
            self.db.commit()
            self.db.refresh(message)
        return message
    
    def get_message(self, message_id: str) -> Optional[Message]:
        """Get message by ID"""
        return self.db.query(Message).filter(Message.id == message_id).first()
    
    # Utility methods
    def user_in_room(self, user_id: str, room_id: str) -> bool:
        """Check if user is in room"""
        participant = self.db.query(RoomParticipant).filter(
            and_(RoomParticipant.room_id == room_id, RoomParticipant.user_id == user_id)
        ).first()
        return participant is not None
