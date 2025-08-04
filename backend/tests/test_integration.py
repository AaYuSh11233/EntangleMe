"""
Integration tests for the quantum messaging system.
"""

import unittest
import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.quantum.teleport import teleport_text_message, text_to_binary, binary_to_text

class TestQuantumMessagingIntegration(unittest.TestCase):
    
    def setUp(self):
        """Set up test client and app"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
    
    def test_send_message_endpoint(self):
        """Test the send-message endpoint"""
        test_data = {
            "sender": "Alice",
            "receiver": "Bob",
            "message": "Hello, Quantum World!"
        }
        
        response = self.client.post('/send-message', 
                                  data=json.dumps(test_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['sender'], 'Alice')
        self.assertEqual(data['receiver'], 'Bob')
        self.assertEqual(data['original_message'], 'Hello, Quantum World!')
        self.assertIn('teleportation_data', data)
        self.assertIn('timestamp', data)
    
    def test_send_message_empty(self):
        """Test sending empty message"""
        test_data = {
            "sender": "Alice",
            "receiver": "Bob",
            "message": ""
        }
        
        response = self.client.post('/send-message', 
                                  data=json.dumps(test_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
    
    def test_send_message_no_data(self):
        """Test sending request without JSON data"""
        response = self.client.post('/send-message')
        self.assertEqual(response.status_code, 400)
    
    def test_receive_message_endpoint(self):
        """Test the receive-message endpoint"""
        # First send a message to get teleportation data
        send_data = {
            "sender": "Alice",
            "receiver": "Bob",
            "message": "Test message"
        }
        
        send_response = self.client.post('/send-message', 
                                        data=json.dumps(send_data),
                                        content_type='application/json')
        send_result = send_response.get_json()
        
        # Now receive the message
        receive_data = {
            "receiver": "Bob",
            "teleportation_data": send_result['teleportation_data']
        }
        
        receive_response = self.client.post('/receive-message', 
                                          data=json.dumps(receive_data),
                                          content_type='application/json')
        
        self.assertEqual(receive_response.status_code, 200)
        receive_result = receive_response.get_json()
        
        self.assertEqual(receive_result['status'], 'success')
        self.assertEqual(receive_result['receiver'], 'Bob')
        self.assertEqual(receive_result['received_message'], 'Test message')
    
    def test_legacy_teleport_endpoint(self):
        """Test the legacy teleport endpoint"""
        test_data = {"state": "0"}
        
        response = self.client.post('/teleport', 
                                  data=json.dumps(test_data),
                                  content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('counts', data)
    
    def test_logs_endpoint(self):
        """Test the logs endpoint"""
        response = self.client.get('/logs')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('logs', data)
        self.assertIn('note', data)
    
    def test_404_error(self):
        """Test 404 error handling"""
        response = self.client.get('/nonexistent-endpoint')
        self.assertEqual(response.status_code, 404)
        data = response.get_json()
        self.assertIn('error', data)
    
    def test_quantum_teleportation_workflow(self):
        """Test the complete quantum teleportation workflow"""
        # Test with various message types
        test_messages = [
            "Hello",
            "A",  # Single character
            "Hello, World! 123",  # Mixed content
            "🚀⚛️🔬",  # Emojis
            "",  # Empty string
        ]
        
        for message in test_messages:
            with self.subTest(message=message):
                result = teleport_text_message(message)
                
                self.assertEqual(result['original_message'], message)
                self.assertEqual(result['reconstructed_message'], message)
                self.assertIn('teleportation_results', result)
                self.assertIn('message_length_chars', result)
                self.assertIn('message_length_bits', result)
                
                # Verify binary conversion
                expected_binary = text_to_binary(message)
                self.assertEqual(result['binary_message'], expected_binary)
                
                # Verify reconstruction
                reconstructed = binary_to_text(result['binary_message'])
                self.assertEqual(reconstructed, message)

if __name__ == "__main__":
    unittest.main() 