from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from datetime import datetime

from app.database.session import get_db
from app.services.quantum_service import QuantumTeleportationService
from app.services.chat_service import ChatService
from app.schemas.quantum import QuantumTeleportRequest, QuantumTeleportResponse, QuantumError
from app.schemas.chat import MessageCreate
from app.core.config import settings

router = APIRouter(prefix="/quantum", tags=["quantum"])

# Initialize quantum service
quantum_service = QuantumTeleportationService(
    simulator_name=settings.QUANTUM_SIMULATOR,
    shots=settings.QUANTUM_SHOTS
)

@router.post("/teleport", response_model=QuantumTeleportResponse)
async def teleport_bit(request: QuantumTeleportRequest, db: Session = Depends(get_db)):
    """
    Perform quantum teleportation of a classical bit between users.
    """
    try:
        # Validate users exist
        chat_service = ChatService(db)
        sender = chat_service.get_user(request.sender_id)
        receiver = chat_service.get_user(request.receiver_id)
        
        if not sender:
            raise HTTPException(status_code=404, detail="Sender not found")
        if not receiver:
            raise HTTPException(status_code=404, detail="Receiver not found")
        
        # Validate room exists and users are in it
        room = chat_service.get_room(request.room_id)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        if not chat_service.user_in_room(request.sender_id, request.room_id):
            raise HTTPException(status_code=403, detail="Sender not in room")
        if not chat_service.user_in_room(request.receiver_id, request.room_id):
            raise HTTPException(status_code=403, detail="Receiver not in room")
        
        # Perform quantum teleportation
        teleportation_result = quantum_service.execute_teleportation(request.classical_bit)
        
        # Create message in database
        message_data = MessageCreate(
            room_id=request.room_id,
            content=request.message_content or f"Teleported bit: {request.classical_bit}",
            quantum_state=str(request.classical_bit)
        )
        
        message = chat_service.create_message(
            message_data=message_data,
            sender_id=request.sender_id
        )
        
        # Update message with teleportation result
        chat_service.update_message_status(
            message_id=message.id,
            status="teleported",
            teleportation_result=teleportation_result
        )
        
        return QuantumTeleportResponse(
            success=teleportation_result["success"],
            sender_id=request.sender_id,
            receiver_id=request.receiver_id,
            sent_bit=teleportation_result["sent_bit"],
            received_bit=teleportation_result["received_bit"],
            classical_bits=teleportation_result["classical_bits"],
            receiver_state=teleportation_result["receiver_state"],
            teleportation_data=teleportation_result["teleportation_data"],
            timestamp=datetime.utcnow(),
            message_id=message.id
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quantum teleportation failed: {str(e)}")

@router.get("/circuit/{bit}")
async def get_circuit_visualization(bit: int):
    """
    Get quantum circuit visualization for teleporting a specific bit.
    """
    try:
        if bit not in (0, 1):
            raise HTTPException(status_code=400, detail="Bit must be 0 or 1")
        
        circuit_data = quantum_service.get_circuit_visualization(bit)
        return {
            "bit": bit,
            "circuit_data": circuit_data,
            "description": f"Quantum teleportation circuit for bit {bit}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate circuit: {str(e)}")

@router.post("/simulate")
async def simulate_teleportation(bit: int):
    """
    Simulate quantum teleportation without storing in database.
    """
    try:
        if bit not in (0, 1):
            raise HTTPException(status_code=400, detail="Bit must be 0 or 1")
        
        result = quantum_service.execute_teleportation(bit)
        return {
            "simulation": True,
            "result": result
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")
