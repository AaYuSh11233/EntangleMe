# EntangleMe - Quantum Teleportation Chat Setup Guide 🌀

## Overview
This is a complete quantum teleportation chat system that simulates quantum entanglement and teleportation of classical bits (0 and 1) using Qiskit and real quantum circuits.

## Features
- ✅ Real quantum teleportation simulation using Qiskit
- ✅ Bell pair entanglement between qubits
- ✅ Classical bit (0/1) teleportation via quantum channel
- ✅ Real-time chat interface
- ✅ Quantum circuit visualization
- ✅ Success probability calculation
- ✅ REST API with FastAPI backend
- ✅ React + TypeScript frontend

## Prerequisites
- Python 3.8+
- Node.js 16+
- Git

## Quick Start

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp env.example .env
# Edit .env with your settings (see below)

# Run the backend
python run.py
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create .env file
cp env.example .env
# Edit .env with your settings (see below)

# Run the frontend
npm run dev
```

### 3. Environment Configuration

#### Backend (.env)
```env
# API Configuration
API_V1_STR=/api/v1
PROJECT_NAME=EntangleME - Quantum Teleportation Chat
VERSION=1.0.0

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=true

# CORS Configuration
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# Database Configuration
DATABASE_URL=sqlite:///./entangleme.db

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379

# JWT Configuration
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Quantum Configuration
QUANTUM_SIMULATOR=qasm_simulator
QUANTUM_SHOTS=1
```

#### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000/api/v1
```

## How It Works

### Quantum Teleportation Protocol
1. **Qubit Preparation**: Prepare qubit 0 in classical bit state (0 or 1)
2. **Bell Pair Creation**: Create entanglement between qubits 1 and 2
3. **Bell Measurement**: Measure qubits 0 and 1 together
4. **Conditional Operations**: Apply gates to qubit 2 based on measurement
5. **Final Measurement**: Measure qubit 2 to recover teleported state

### API Endpoints

#### Quantum Teleportation
- `POST /api/v1/quantum/teleport` - Perform quantum teleportation
- `GET /api/v1/quantum/circuit/{bit}` - Get circuit visualization
- `POST /api/v1/quantum/simulate` - Simulate teleportation

#### Chat System
- `POST /api/v1/chat/users` - Create user
- `POST /api/v1/chat/rooms` - Create room
- `GET /api/v1/chat/rooms/{room_id}/participants` - Get room participants
- `GET /api/v1/chat/rooms/{room_id}/messages` - Get messages
- `DELETE /api/v1/chat/rooms/{room_id}/participants/{user_id}` - Leave room

## Usage

1. **Start both backend and frontend**
2. **Open browser to** `http://localhost:5173`
3. **Enter username** and click "Get Started"
4. **Wait for second user** to join the room
5. **Send bits (0 or 1)** to perform quantum teleportation
6. **View quantum details** by clicking the "View Quantum Details" button

## Testing

### Backend Tests
```bash
cd backend
python test_quantum.py
```

### Frontend Connection Test
```bash
cd frontend
node test-connection.js
```

## Architecture

### Backend (FastAPI + Qiskit)
- **Quantum Service**: Handles quantum teleportation simulation
- **Chat Service**: Manages users, rooms, and messages
- **Database**: SQLite with SQLAlchemy ORM
- **API**: RESTful endpoints with automatic documentation

### Frontend (React + TypeScript)
- **Real-time Updates**: Polling-based message updates
- **Quantum Visualization**: Circuit diagrams and teleportation details
- **Modern UI**: Tailwind CSS + shadcn/ui components
- **Type Safety**: Full TypeScript integration

## Quantum Circuit Details

The system implements the standard quantum teleportation protocol:

```
Step 1: Prepare |ψ⟩ = α|0⟩ + β|1⟩ on qubit 0
Step 2: Create Bell pair |Φ⁺⟩ = (|00⟩ + |11⟩)/√2 on qubits 1,2
Step 3: Bell measurement on qubits 0,1
Step 4: Conditional operations on qubit 2
Step 5: Measure qubit 2 to recover |ψ⟩
```

## Troubleshooting

### Common Issues

1. **Backend won't start**
   - Check Python version (3.8+)
   - Verify all dependencies installed
   - Check .env configuration

2. **Frontend can't connect**
   - Ensure backend is running on port 8000
   - Check CORS settings in backend
   - Verify VITE_API_URL in frontend .env

3. **Quantum simulation fails**
   - Check Qiskit installation
   - Verify quantum simulator configuration
   - Check console for error messages

### Debug Mode
- Backend: Set `DEBUG=true` in .env
- Frontend: Check browser console for API errors

## Development

### Adding New Features
1. **Backend**: Add endpoints in `app/api/`
2. **Frontend**: Add components in `src/components/`
3. **Types**: Update TypeScript interfaces
4. **Testing**: Add tests for new functionality

### Database Schema
- **Users**: username, email, online status
- **Rooms**: name, participants, activity
- **Messages**: content, quantum state, teleportation results

## License
MIT License - See LICENSE file for details

## Contributing
1. Fork the repository
2. Create feature branch
3. Make changes
4. Add tests
5. Submit pull request

---

**Enjoy quantum teleportation! 🌀✨**
