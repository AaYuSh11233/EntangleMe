"""
Tests for the quantum text messaging system.
"""

import unittest
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.quantum.teleport import (
    teleport_text_message,
    teleport_single_bit,
    text_to_binary,
    binary_to_text
)
from app.utils.formatter import (
    format_statevector,
    format_message_stats,
    format_binary_string
)

class TestQuantumMessaging(unittest.TestCase):
    
    def test_text_to_binary_conversion(self):
        """Test text to binary conversion"""
        # Test simple text
        self.assertEqual(text_to_binary("A"), "01000001")
        self.assertEqual(text_to_binary("Hello"), "0100100001100101011011000110110001101111")
        
        # Test empty string
        self.assertEqual(text_to_binary(""), "")
        
        # Test special characters
        self.assertEqual(text_to_binary("!"), "00100001")
    
    def test_binary_to_text_conversion(self):
        """Test binary to text conversion"""
        # Test simple text
        self.assertEqual(binary_to_text("01000001"), "A")
        self.assertEqual(binary_to_text("0100100001100101011011000110110001101111"), "Hello")
        
        # Test empty string
        self.assertEqual(binary_to_text(""), "")
        
        # Test round trip
        original = "Hello World!"
        binary = text_to_binary(original)
        reconstructed = binary_to_text(binary)
        self.assertEqual(original, reconstructed)
    
    def test_single_bit_teleportation(self):
        """Test single bit teleportation"""
        # Test teleporting "0"
        result_0 = teleport_single_bit("0")
        self.assertIn("input", result_0)
        self.assertEqual(result_0["input"], "0")
        self.assertIn("counts", result_0)
        self.assertIn("statevector", result_0)
        
        # Test teleporting "1"
        result_1 = teleport_single_bit("1")
        self.assertIn("input", result_1)
        self.assertEqual(result_1["input"], "1")
        self.assertIn("counts", result_1)
        self.assertIn("statevector", result_1)
    
    def test_text_message_teleportation(self):
        """Test text message teleportation"""
        # Test short message
        message = "Hi"
        result = teleport_text_message(message)
        
        self.assertIn("original_message", result)
        self.assertEqual(result["original_message"], message)
        
        self.assertIn("binary_message", result)
        self.assertIn("reconstructed_message", result)
        self.assertEqual(result["reconstructed_message"], message)
        
        self.assertIn("teleportation_results", result)
        self.assertIsInstance(result["teleportation_results"], list)
        
        self.assertIn("message_length_bits", result)
        self.assertIn("message_length_chars", result)
        self.assertEqual(result["message_length_chars"], len(message))
    
    def test_formatting_functions(self):
        """Test formatting utility functions"""
        # Test statevector formatting
        test_statevector = [0.7071, 0.7071]
        formatted = format_statevector(test_statevector)
        self.assertEqual(formatted, [0.7071, 0.7071])
        
        # Test message stats
        message = "Hello"
        stats = format_message_stats(message)
        self.assertIn("length_chars", stats)
        self.assertEqual(stats["length_chars"], 5)
        self.assertIn("length_bits", stats)
        self.assertIn("binary_preview", stats)
        
        # Test binary string formatting
        binary = "0100000101000010"
        formatted_binary = format_binary_string(binary)
        self.assertEqual(formatted_binary, "01000001 01000010")
    
    def test_edge_cases(self):
        """Test edge cases and error handling"""
        # Test empty message
        result = teleport_text_message("")
        self.assertEqual(result["original_message"], "")
        self.assertEqual(result["reconstructed_message"], "")
        
        # Test single character
        result = teleport_text_message("A")
        self.assertEqual(result["original_message"], "A")
        self.assertEqual(result["reconstructed_message"], "A")
        
        # Test special characters
        special_chars = "!@#$%^&*()"
        result = teleport_text_message(special_chars)
        self.assertEqual(result["original_message"], special_chars)
        self.assertEqual(result["reconstructed_message"], special_chars)

if __name__ == "__main__":
    unittest.main() 