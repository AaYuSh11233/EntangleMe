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
- ✅ Automatic database reset functionality

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
cp .env.example .env
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
cp .env.example .env
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

# CORS Configuration (comma-separated list)
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8000,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:5173,http://127.0.0.1:8000,http://127.0.0.1:8080,https://entangleme.vercel.app,https://entangleme.onrender.com

# Database Configuration
DATABASE_URL=sqlite:///./entangleme.db

# Database Reset Configuration
# Set to 'true' to reset database on startup (useful for development/testing)
RESET_DB=false
# Environment: 'development' or 'production'
ENVIRONMENT=development

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
3. **Bell Measurement**: Perform Bell measurement on qubits 0 and 1
4. **Conditional Operations**: Apply conditional operations on qubit 2
5. **Final Measurement**: Measure qubit 2 to recover the teleported state

### Database Reset Functionality

The application includes automatic database reset functionality for production deployments:

#### Environment Variables

- `RESET_DB`: Set to `true` to reset database on startup
- `ENVIRONMENT`: Set to `production` for production environment

#### Usage

1. **Development**:
   ```bash
   # Manual reset
   python scripts/reset_db.py
   
   # Automatic reset on startup
   RESET_DB=true python run.py
   ```

2. **Production**:
   ```bash
   # Set environment variables in Render
   RESET_DB=true
   ENVIRONMENT=production
   ```

## Deployment

### Backend (Render)
1. **Connect repository** to Render
2. **Set environment variables**:
   ```bash
   HOST=0.0.0.0
   PORT=8000
   DEBUG=False
   RESET_DB=true
   ENVIRONMENT=production
   SECRET_KEY=your-super-secret-key
   DATABASE_URL=your-database-url
   REDIS_URL=your-redis-url
   ```
3. **Deploy** → `https://entangleme.onrender.com`

### Frontend (Vercel)
1. **Connect repository** to Vercel
2. **Set environment variables**:
   ```bash
   VITE_API_URL=https://entangleme.onrender.com/api/v1
   ```
3. **Deploy** → `https://entangleme.vercel.app`

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

### Database Issues
- **User conflicts**: Use `RESET_DB=true` to reset database
- **Connection issues**: Check `DATABASE_URL` configuration
- **Production reset**: Set `ENVIRONMENT=production` and `RESET_DB=true`

### CORS Issues
- **Frontend connection**: Check `BACKEND_CORS_ORIGINS` configuration
- **Production domains**: Ensure production URLs are in CORS list

## Support

For issues with:
- **Backend deployment**: Check Render logs and environment variables
- **Frontend deployment**: Check Vercel logs and environment variables
- **Database reset**: Use the reset script or environment variables
