from qiskit import QuantumCircuit, ClassicalRegister, QuantumRegister, Aer, execute
from qiskit.visualization import plot_circuit_layout
from qiskit.quantum_info import Statevector
import numpy as np
from typing import Dict, Any, Tuple
import json
from datetime import datetime

class QuantumTeleportationService:
    def __init__(self, simulator_name: str = "qasm_simulator", shots: int = 1):
        self.simulator_name = simulator_name
        self.shots = shots
        self.backend = Aer.get_backend(simulator_name)
    
    def create_teleportation_circuit(self, classical_bit: int) -> Tuple[QuantumCircuit, Dict[str, Any]]:
        """
        Create a quantum teleportation circuit for the given classical bit.
        Returns the circuit and circuit metadata.
        """
        if classical_bit not in (0, 1):
            raise ValueError("Only classical bit 0 or 1 allowed.")
        
        # Create quantum and classical registers
        qreg = QuantumRegister(3, 'q')
        creg = ClassicalRegister(3, 'c')
        circuit = QuantumCircuit(qreg, creg)
        
        # Circuit metadata for visualization
        circuit_data = {
            "steps": [],
            "gates": [],
            "measurements": [],
            "initial_state": f"|{classical_bit}⟩",
            "final_state": None
        }
        
        # Step 1: Prepare qubit 0 in classical_bit state
        if classical_bit == 1:
            circuit.x(qreg[0])
            circuit_data["gates"].append({"gate": "X", "qubit": 0, "step": 1})
        circuit_data["steps"].append({
            "step": 1,
            "description": f"Prepare qubit 0 in state |{classical_bit}⟩",
            "qubits": [0]
        })
        
        # Step 2: Create Bell pair (entanglement between qubit 1 and 2)
        circuit.h(qreg[1])
        circuit.cx(qreg[1], qreg[2])
        circuit_data["gates"].extend([
            {"gate": "H", "qubit": 1, "step": 2},
            {"gate": "CX", "control": 1, "target": 2, "step": 2}
        ])
        circuit_data["steps"].append({
            "step": 2,
            "description": "Create Bell pair (entanglement between qubits 1 and 2)",
            "qubits": [1, 2]
        })
        
        # Step 3: Bell measurement on qubit 0 and 1
        circuit.cx(qreg[0], qreg[1])
        circuit.h(qreg[0])
        circuit.measure([qreg[0], qreg[1]], [creg[0], creg[1]])
        circuit_data["gates"].extend([
            {"gate": "CX", "control": 0, "target": 1, "step": 3},
            {"gate": "H", "qubit": 0, "step": 3}
        ])
        circuit_data["measurements"].extend([
            {"qubit": 0, "classical_bit": 0, "step": 3},
            {"qubit": 1, "classical_bit": 1, "step": 3}
        ])
        circuit_data["steps"].append({
            "step": 3,
            "description": "Bell measurement on qubits 0 and 1",
            "qubits": [0, 1]
        })
        
        # Step 4: Conditional operations on qubit 2
        circuit.cx(qreg[1], qreg[2])
        circuit.cz(qreg[0], qreg[2])
        circuit_data["gates"].extend([
            {"gate": "CX", "control": 1, "target": 2, "step": 4},
            {"gate": "CZ", "control": 0, "target": 2, "step": 4}
        ])
        circuit_data["steps"].append({
            "step": 4,
            "description": "Conditional operations on qubit 2 based on measurement results",
            "qubits": [2]
        })
        
        # Step 5: Measure qubit 2
        circuit.measure(qreg[2], creg[2])
        circuit_data["measurements"].append({
            "qubit": 2, "classical_bit": 2, "step": 5
        })
        circuit_data["steps"].append({
            "step": 5,
            "description": "Measure qubit 2 to recover the teleported state",
            "qubits": [2]
        })
        
        return circuit, circuit_data
    
    def execute_teleportation(self, classical_bit: int) -> Dict[str, Any]:
        """
        Execute quantum teleportation and return detailed results.
        """
        try:
            # Create circuit
            circuit, circuit_data = self.create_teleportation_circuit(classical_bit)
            
            # Execute the circuit
            job = execute(circuit, self.backend, shots=self.shots, memory=True)
            result = job.result()
            memory = result.get_memory()
            
            # Get measurement results
            measurement_string = memory[0]  # e.g., "010"
            classical_bits = measurement_string
            received_bit = int(measurement_string[2])  # Last bit is the teleported state
            
            # Verify teleportation success
            success = received_bit == classical_bit
            
            # Generate circuit diagram
            circuit_diagram = str(circuit)
            
            # Update circuit data with results
            circuit_data["final_state"] = f"|{received_bit}⟩"
            circuit_data["measurement_results"] = {
                "classical_bits": classical_bits,
                "received_bit": received_bit,
                "success": success
            }
            
            # Calculate success probability (for multiple shots)
            if self.shots > 1:
                counts = result.get_counts()
                success_count = counts.get(measurement_string, 0)
                success_probability = success_count / self.shots
            else:
                success_probability = 1.0 if success else 0.0
            
            return {
                "success": success,
                "sent_bit": classical_bit,
                "received_bit": received_bit,
                "classical_bits": classical_bits,
                "receiver_state": f"|{received_bit}⟩",
                "circuit_diagram": circuit_diagram,
                "circuit_data": circuit_data,
                "success_probability": success_probability,
                "measurement_results": {
                    "classical_bits": classical_bits,
                    "received_bit": received_bit,
                    "success": success
                },
                "teleportation_data": {
                    "circuit": circuit_data,
                    "measurements": circuit_data["measurements"],
                    "gates": circuit_data["gates"],
                    "steps": circuit_data["steps"]
                }
            }
            
        except Exception as e:
            raise Exception(f"Quantum teleportation failed: {str(e)}")
    
    def get_circuit_visualization(self, classical_bit: int) -> Dict[str, Any]:
        """
        Get detailed circuit visualization data.
        """
        circuit, circuit_data = self.create_teleportation_circuit(classical_bit)
        
        return {
            "circuit_text": str(circuit),
            "circuit_data": circuit_data,
            "num_qubits": 3,
            "num_classical_bits": 3,
            "depth": circuit.depth(),
            "gate_count": circuit.count_ops()
        }
