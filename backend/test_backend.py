#!/usr/bin/env python3
"""
Test script for backend API endpoints
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_backend():
    """Test backend API endpoints"""
    print("🧪 Testing Backend API...")
    print("=" * 50)
    
    try:
        # Test health endpoint
        print("📡 Testing health endpoint...")
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
        
        # Test quantum circuit endpoint
        print("\n📡 Testing quantum circuit endpoint...")
        response = requests.get(f"{BASE_URL}/api/v1/quantum/circuit/0")
        if response.status_code == 200:
            print("✅ Quantum circuit endpoint working")
            data = response.json()
            print(f"   Bit: {data.get('bit')}")
        else:
            print(f"❌ Quantum circuit failed: {response.status_code}")
        
        # Test user creation
        print("\n📡 Testing user creation...")
        user_data = {
            "username": "testuser",
            "email": "test@example.com"
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/users",
            json=user_data,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print("✅ User creation working")
            user = response.json()
            print(f"   User ID: {user.get('id')}")
            print(f"   Username: {user.get('username')}")
        else:
            print(f"❌ User creation failed: {response.status_code}")
            print(f"   Error: {response.text}")
        
        # Test room creation
        print("\n📡 Testing room creation...")
        room_data = {
            "name": "Test Room",
            "participant_ids": []
        }
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/rooms",
            json=room_data,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            print("✅ Room creation working")
            room = response.json()
            print(f"   Room ID: {room.get('id')}")
            print(f"   Room Name: {room.get('name')}")
        else:
            print(f"❌ Room creation failed: {response.status_code}")
            print(f"   Error: {response.text}")
        
        print("\n🎉 Backend API tests completed!")
        print("=" * 50)
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_backend()
