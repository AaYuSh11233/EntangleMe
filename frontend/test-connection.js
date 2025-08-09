// Simple test script to verify backend connection
const API_BASE_URL = 'http://localhost:8000/api/v1';

async function testConnection() {
  console.log('🧪 Testing backend connection...');
  
  try {
    // Test health endpoint
    const healthResponse = await fetch(`${API_BASE_URL.replace('/api/v1', '')}/health`);
    if (healthResponse.ok) {
      console.log('✅ Backend is running');
    } else {
      console.log('❌ Backend health check failed');
    }
    
    // Test quantum circuit endpoint
    const circuitResponse = await fetch(`${API_BASE_URL}/quantum/circuit/0`);
    if (circuitResponse.ok) {
      console.log('✅ Quantum API is working');
    } else {
      console.log('❌ Quantum API failed');
    }
    
  } catch (error) {
    console.error('❌ Connection failed:', error);
  }
}

testConnection();
