from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database.session import get_db
from app.services.chat_service import ChatService
from app.schemas.chat import (
    UserCreate, UserResponse, RoomCreate, RoomResponse, 
    MessageCreate, MessageResponse, JoinRoomRequest, LeaveRoomRequest
)

router = APIRouter(prefix="/chat", tags=["chat"])

# User endpoints
@router.post("/users", response_model=UserResponse)
async def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    chat_service = ChatService(db)
    
    # Check if username already exists
    existing_user = chat_service.get_user_by_username(user_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user = chat_service.create_user(user_data)
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_online=user.is_online,
        last_seen=user.last_seen,
        created_at=user.created_at
    )

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: Session = Depends(get_db)):
    """Get user by ID"""
    chat_service = ChatService(db)
    user = chat_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_online=user.is_online,
        last_seen=user.last_seen,
        created_at=user.created_at
    )

@router.put("/users/{user_id}/status")
async def update_user_status(user_id: str, is_online: bool, db: Session = Depends(get_db)):
    """Update user online status"""
    chat_service = ChatService(db)
    user = chat_service.update_user_status(user_id, is_online)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User status updated", "user_id": user_id, "is_online": is_online}

@router.get("/users/online", response_model=List[UserResponse])
async def get_online_users(db: Session = Depends(get_db)):
    """Get all online users"""
    chat_service = ChatService(db)
    users = chat_service.get_online_users()
    return [
        UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            is_online=user.is_online,
            last_seen=user.last_seen,
            created_at=user.created_at
        ) for user in users
    ]

# Room endpoints
@router.get("/rooms", response_model=List[RoomResponse])
async def get_all_rooms(db: Session = Depends(get_db)):
    """Get all rooms"""
    chat_service = ChatService(db)
    rooms = chat_service.get_all_rooms()
    
    room_responses = []
    for room in rooms:
        participants = chat_service.get_room_participants(room.id)
        participant_responses = [
            UserResponse(
                id=p.id,
                username=p.username,
                email=p.email,
                is_online=p.is_online,
                last_seen=p.last_seen,
                created_at=p.created_at
            ) for p in participants
        ]
        
        room_responses.append(RoomResponse(
            id=room.id,
            name=room.name,
            created_by=room.created_by,
            created_at=room.created_at,
            last_activity=room.last_activity,
            participants=participant_responses
        ))
    
    return room_responses

@router.post("/rooms", response_model=RoomResponse)
async def create_room(room_data: RoomCreate, db: Session = Depends(get_db)):
    """Create a new chat room"""
    chat_service = ChatService(db)
    
    # Validate that creator exists
    creator = chat_service.get_user(room_data.participant_ids[0] if room_data.participant_ids else None)
    if not creator:
        raise HTTPException(status_code=404, detail="Creator not found")
    
    room = chat_service.create_room(room_data, creator.id)
    
    # Get participants for response
    participants = chat_service.get_room_participants(room.id)
    participant_responses = [
        UserResponse(
            id=p.id,
            username=p.username,
            email=p.email,
            is_online=p.is_online,
            last_seen=p.last_seen,
            created_at=p.created_at
        ) for p in participants
    ]
    
    return RoomResponse(
        id=room.id,
        name=room.name,
        created_by=room.created_by,
        created_at=room.created_at,
        last_activity=room.last_activity,
        participants=participant_responses
    )

@router.get("/rooms/{room_id}", response_model=RoomResponse)
async def get_room(room_id: str, db: Session = Depends(get_db)):
    """Get room by ID"""
    chat_service = ChatService(db)
    room = chat_service.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    participants = chat_service.get_room_participants(room.id)
    participant_responses = [
        UserResponse(
            id=p.id,
            username=p.username,
            email=p.email,
            is_online=p.is_online,
            last_seen=p.last_seen,
            created_at=p.created_at
        ) for p in participants
    ]
    
    return RoomResponse(
        id=room.id,
        name=room.name,
        created_by=room.created_by,
        created_at=room.created_at,
        last_activity=room.last_activity,
        participants=participant_responses
    )

@router.get("/rooms/{room_id}/participants", response_model=List[UserResponse])
async def get_room_participants(room_id: str, db: Session = Depends(get_db)):
    """Get all participants in a room"""
    chat_service = ChatService(db)
    
    # Validate room exists
    room = chat_service.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    participants = chat_service.get_room_participants(room_id)
    return [
        UserResponse(
            id=p.id,
            username=p.username,
            email=p.email,
            is_online=p.is_online,
            last_seen=p.last_seen,
            created_at=p.created_at
        ) for p in participants
    ]

@router.delete("/rooms/{room_id}/participants/{user_id}")
async def remove_room_participant(room_id: str, user_id: str, db: Session = Depends(get_db)):
    """Remove a participant from a room"""
    chat_service = ChatService(db)
    success = chat_service.remove_user_from_room(room_id, user_id)
    if not success:
        raise HTTPException(status_code=400, detail="User not in room or room not found")
    
    return {"message": "User removed from room", "room_id": room_id, "user_id": user_id}

@router.get("/users/{user_id}/rooms", response_model=List[RoomResponse])
async def get_user_rooms(user_id: str, db: Session = Depends(get_db)):
    """Get all rooms for a user"""
    chat_service = ChatService(db)
    rooms = chat_service.get_user_rooms(user_id)
    
    room_responses = []
    for room in rooms:
        participants = chat_service.get_room_participants(room.id)
        participant_responses = [
            UserResponse(
                id=p.id,
                username=p.username,
                email=p.email,
                is_online=p.is_online,
                last_seen=p.last_seen,
                created_at=p.created_at
            ) for p in participants
        ]
        
        room_responses.append(RoomResponse(
            id=room.id,
            name=room.name,
            created_by=room.created_by,
            created_at=room.created_at,
            last_activity=room.last_activity,
            participants=participant_responses
        ))
    
    return room_responses

@router.post("/rooms/join")
async def join_room(request: JoinRoomRequest, db: Session = Depends(get_db)):
    """Join a room"""
    chat_service = ChatService(db)
    success = chat_service.add_user_to_room(request.room_id, request.user_id)
    if not success:
        raise HTTPException(status_code=400, detail="User already in room or room not found")
    
    return {"message": "User joined room", "room_id": request.room_id, "user_id": request.user_id}

@router.post("/rooms/leave")
async def leave_room(request: LeaveRoomRequest, db: Session = Depends(get_db)):
    """Leave a room"""
    chat_service = ChatService(db)
    success = chat_service.remove_user_from_room(request.room_id, request.user_id)
    if not success:
        raise HTTPException(status_code=400, detail="User not in room")
    
    return {"message": "User left room", "room_id": request.room_id, "user_id": request.user_id}

# Message endpoints
@router.post("/messages", response_model=MessageResponse)
async def create_message(message_data: MessageCreate, sender_id: str, db: Session = Depends(get_db)):
    """Create a new message"""
    chat_service = ChatService(db)
    
    # Validate sender exists
    sender = chat_service.get_user(sender_id)
    if not sender:
        raise HTTPException(status_code=404, detail="Sender not found")
    
    # Validate room exists and sender is in room
    room = chat_service.get_room(message_data.room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    if not chat_service.user_in_room(sender_id, message_data.room_id):
        raise HTTPException(status_code=403, detail="Sender not in room")
    
    message = chat_service.create_message(message_data, sender_id)
    
    return MessageResponse(
        id=message.id,
        room_id=message.room_id,
        sender_id=message.sender_id,
        sender_username=sender.username,
        content=message.content,
        quantum_state=message.quantum_state,
        teleportation_result=message.teleportation_result,
        status=message.status,
        created_at=message.created_at
    )

@router.get("/rooms/{room_id}/messages", response_model=List[MessageResponse])
async def get_room_messages(
    room_id: str, 
    limit: int = 50, 
    offset: int = 0, 
    db: Session = Depends(get_db)
):
    """Get messages for a room"""
    chat_service = ChatService(db)
    
    # Validate room exists
    room = chat_service.get_room(room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    messages = chat_service.get_room_messages(room_id, limit, offset)
    
    message_responses = []
    for message in messages:
        sender = chat_service.get_user(message.sender_id)
        message_responses.append(MessageResponse(
            id=message.id,
            room_id=message.room_id,
            sender_id=message.sender_id,
            sender_username=sender.username if sender else "Unknown",
            content=message.content,
            quantum_state=message.quantum_state,
            teleportation_result=message.teleportation_result,
            status=message.status,
            created_at=message.created_at
        ))
    
    return message_responses

@router.get("/messages/{message_id}", response_model=MessageResponse)
async def get_message(message_id: str, db: Session = Depends(get_db)):
    """Get message by ID"""
    chat_service = ChatService(db)
    message = chat_service.get_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    
    sender = chat_service.get_user(message.sender_id)
    return MessageResponse(
        id=message.id,
        room_id=message.room_id,
        sender_id=message.sender_id,
        sender_username=sender.username if sender else "Unknown",
        content=message.content,
        quantum_state=message.quantum_state,
        teleportation_result=message.teleportation_result,
        status=message.status,
        created_at=message.created_at
    )
