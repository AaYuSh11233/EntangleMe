from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class QuantumTeleportRequest(BaseModel):
    sender_id: str = Field(..., description="ID of the sender")
    receiver_id: str = Field(..., description="ID of the receiver")
    classical_bit: int = Field(..., ge=0, le=1, description="Classical bit to teleport (0 or 1)")
    room_id: str = Field(..., description="Room ID where teleportation occurs")
    message_content: Optional[str] = Field(None, description="Optional text message")

class QuantumTeleportResponse(BaseModel):
    success: bool
    sender_id: str
    receiver_id: str
    sent_bit: int
    received_bit: int
    classical_bits: str = Field(..., description="Measurement results as binary string")
    receiver_state: str = Field(..., description="Final state of receiver qubit")
    teleportation_data: Dict[str, Any] = Field(..., description="Complete teleportation circuit data")
    timestamp: datetime
    message_id: Optional[str] = None

class QuantumCircuitData(BaseModel):
    circuit_diagram: str
    gate_sequence: list
    measurement_results: Dict[str, Any]
    final_state: str

class QuantumError(BaseModel):
    error: str
    details: Optional[str] = None
