#!/usr/bin/env python3
"""
Test script for quantum teleportation functionality
"""

from app.services.quantum_service import QuantumTeleportationService

def test_quantum_teleportation():
    """Test quantum teleportation for both 0 and 1 bits"""
    print("🧪 Testing Quantum Teleportation...")
    print("=" * 50)
    
    quantum_service = QuantumTeleportationService()
    
    # Test teleporting bit 0
    print("📡 Testing teleportation of bit 0...")
    result_0 = quantum_service.execute_teleportation(0)
    print(f"✅ Sent: {result_0['sent_bit']}, Received: {result_0['received_bit']}")
    print(f"📊 Success: {result_0['success']}")
    print(f"🔢 Classical bits: {result_0['classical_bits']}")
    print(f"🎯 Receiver state: {result_0['receiver_state']}")
    print()
    
    # Test teleporting bit 1
    print("📡 Testing teleportation of bit 1...")
    result_1 = quantum_service.execute_teleportation(1)
    print(f"✅ Sent: {result_1['sent_bit']}, Received: {result_1['received_bit']}")
    print(f"📊 Success: {result_1['success']}")
    print(f"🔢 Classical bits: {result_1['classical_bits']}")
    print(f"🎯 Receiver state: {result_1['receiver_state']}")
    print()
    
    # Test circuit visualization
    print("🔬 Testing circuit visualization...")
    circuit_data = quantum_service.get_circuit_visualization(0)
    print(f"📐 Circuit depth: {circuit_data['depth']}")
    print(f"⚡ Gate count: {circuit_data['gate_count']}")
    print(f"🔢 Number of qubits: {circuit_data['num_qubits']}")
    print()
    
    print("🎉 All tests completed successfully!")
    print("=" * 50)

if __name__ == "__main__":
    test_quantum_teleportation()
