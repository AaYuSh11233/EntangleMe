from classiq import ModelDesigner, create_model, get_qiskit_circuit
from classiq.builtins import QuantumTeleportationModel
from qiskit import QuantumCircuit
import logging
import os
from config import Config

logger = logging.getLogger(__name__)

def build_teleportation_circuit_classiq(input_state: str) -> QuantumCircuit:
    """
    Build a quantum teleportation circuit using Classiq's auto-generation.
    
    Args:
        input_state (str): The input state to encode ("0", "1", or text character)
    
    Returns:
        QuantumCircuit: The generated teleportation circuit
    """
    try:
        # Check if Classiq API key is configured
        if not Config.CLASSIQ_API_KEY:
            logger.warning("Classiq API key not found. Using manual circuit construction.")
            return build_teleportation_circuit_manual(input_state)
        
        logger.info(f"Generating teleportation circuit for input: {input_state}")
        
        # Generate teleportation circuit from Classiq
        model = QuantumTeleportationModel()
        model_json = create_model(model)
        designer = ModelDesigner(model_json)
        
        # Save circuit to file
        circuit_file = f"teleportation_{input_state}.json"
        designer.build_circuit(circuit_file)
        
        # Get Qiskit circuit
        qc = get_qiskit_circuit(circuit_file)
        
        # Encode the input qubit based on the input state
        if input_state == "1":
            qc.x(0)
        elif input_state == "0":
            pass  # Already in |0⟩ state
        else:
            # For text characters, we can encode them as superposition states
            # This is a simplified approach - in practice, you'd want more sophisticated encoding
            char_code = ord(input_state)
            if char_code % 2 == 1:
                qc.x(0)
        
        logger.info(f"Successfully generated Classiq circuit for input: {input_state}")
        return qc
        
    except Exception as e:
        logger.error(f"Failed to generate Classiq circuit: {e}")
        logger.info("Falling back to manual circuit construction")
        return build_teleportation_circuit_manual(input_state)

def build_teleportation_circuit_manual(input_state: str) -> QuantumCircuit:
    """
    Build a quantum teleportation circuit manually using Qiskit.
    This is used as a fallback when Classiq is not available.
    
    Args:
        input_state (str): The input state to encode
    
    Returns:
        QuantumCircuit: The manually constructed teleportation circuit
    """
    from qiskit import QuantumRegister, ClassicalRegister
    
    # Create quantum circuit with 3 qubits and 2 classical bits
    qr = QuantumRegister(3, 'q')
    cr = ClassicalRegister(2, 'c')
    qc = QuantumCircuit(qr, cr)
    
    # Prepare the input state (qubit 0)
    if input_state == "1":
        qc.x(qr[0])
    elif input_state == "0":
        pass  # Already in |0⟩ state
    else:
        # For text characters, encode as binary
        char_code = ord(input_state)
        if char_code % 2 == 1:
            qc.x(qr[0])
    
    # Create Bell pair between qubits 1 and 2
    qc.h(qr[1])
    qc.cx(qr[1], qr[2])
    
    # Bell measurement on qubits 0 and 1
    qc.cx(qr[0], qr[1])
    qc.h(qr[0])
    qc.measure(qr[0], cr[0])
    qc.measure(qr[1], cr[1])
    
    # Apply correction gates based on measurement results
    qc.x(qr[2]).c_if(cr[1], 1)
    qc.z(qr[2]).c_if(cr[0], 1)
    
    return qc

def build_teleportation_circuit(input_state: str) -> QuantumCircuit:
    """
    Main function to build teleportation circuit.
    Tries Classiq first, falls back to manual construction.
    
    Args:
        input_state (str): The input state to encode
    
    Returns:
        QuantumCircuit: The teleportation circuit
    """
    return build_teleportation_circuit_classiq(input_state)
