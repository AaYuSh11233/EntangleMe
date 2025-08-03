"""
Utility functions for formatting quantum states and messages in EntangleMe.
"""

import numpy as np
from typing import List, Dict, Any, Union

def format_statevector(statevector) -> List[float]:
    """
    Format quantum statevector for API response.
    
    Args:
        statevector: Quantum statevector from Qiskit
        
    Returns:
        List[float]: Formatted statevector with rounded values
    """
    if hasattr(statevector, 'data'):
        # Handle Qiskit statevector objects
        return [round(abs(x), 4) for x in statevector.data]
    elif isinstance(statevector, (list, np.ndarray)):
        # Handle list or numpy array
        return [round(abs(float(x)), 4) for x in statevector]
    else:
        return [round(abs(float(statevector)), 4)]

def format_teleportation_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format teleportation result for API response.
    
    Args:
        result: Raw teleportation result
        
    Returns:
        Dict[str, Any]: Formatted result
    """
    formatted = result.copy()
    
    # Format statevector if present
    if 'statevector' in formatted:
        formatted['statevector'] = format_statevector(formatted['statevector'])
    
    # Format counts if present
    if 'counts' in formatted:
        formatted['counts'] = {str(k): int(v) for k, v in formatted['counts'].items()}
    
    return formatted

def format_binary_string(binary: str, chunk_size: int = 8) -> str:
    """
    Format binary string with spaces for readability.
    
    Args:
        binary: Binary string
        chunk_size: Size of chunks to separate with spaces
        
    Returns:
        str: Formatted binary string
    """
    return ' '.join([binary[i:i+chunk_size] for i in range(0, len(binary), chunk_size)])

def format_message_stats(message: str) -> Dict[str, Any]:
    """
    Generate statistics for a message.
    
    Args:
        message: Input message
        
    Returns:
        Dict[str, Any]: Message statistics
    """
    binary = ''.join(format(ord(char), '08b') for char in message)
    
    return {
        'length_chars': len(message),
        'length_bits': len(binary),
        'binary_preview': binary[:32] + '...' if len(binary) > 32 else binary,
        'unique_chars': len(set(message)),
        'avg_bits_per_char': len(binary) / len(message) if message else 0
    }

def format_quantum_circuit_info(circuit) -> Dict[str, Any]:
    """
    Extract and format information from a quantum circuit.
    
    Args:
        circuit: Qiskit quantum circuit
        
    Returns:
        Dict[str, Any]: Circuit information
    """
    return {
        'num_qubits': circuit.num_qubits,
        'num_clbits': circuit.num_clbits,
        'depth': circuit.depth(),
        'size': circuit.size(),
        'instructions': len(circuit.data)
    }

def format_log_entry(entry: str) -> Dict[str, str]:
    """
    Parse and format a log entry.
    
    Args:
        entry: Raw log entry string
        
    Returns:
        Dict[str, str]: Formatted log entry
    """
    try:
        # Split log entry into components
        parts = entry.strip().split(' - ', 2)
        if len(parts) >= 3:
            timestamp, level, message = parts[0], parts[1], parts[2]
            return {
                'timestamp': timestamp,
                'level': level,
                'message': message
            }
        else:
            return {
                'timestamp': '',
                'level': 'INFO',
                'message': entry.strip()
            }
    except Exception:
        return {
            'timestamp': '',
            'level': 'INFO',
            'message': entry.strip()
        }
