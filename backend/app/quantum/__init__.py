"""
Quantum Teleportation Module for EntangleMe

This module provides quantum teleportation functionality for text messaging.
It includes both manual Qiskit circuit construction and Classiq auto-generation.

Key Components:
- teleport.py: Core teleportation logic for text messages
- classiq_generator.py: Auto-generated circuits using Classiq
"""

from .teleport import (
    teleport_text_message,
    teleport_single_bit,
    teleport_classically,
    text_to_binary,
    binary_to_text,
    build_teleportation_circuit
)

from .classiq_generator import build_teleportation_circuit_classiq

__all__ = [
    'teleport_text_message',
    'teleport_single_bit', 
    'teleport_classically',
    'text_to_binary',
    'binary_to_text',
    'build_teleportation_circuit',
    'build_teleportation_circuit_classiq'
]
