# EntangleME Backend - Quantum Teleportation Chat API

A professional FastAPI backend for the EntangleME quantum teleportation chat application. This backend provides quantum teleportation simulation, real-time chat functionality, and secure message transmission using quantum principles.

## Features

- **Quantum Teleportation Simulation**: Real quantum circuit execution using Qiskit
- **Real-time Chat**: User management, room creation, and message handling
- **RESTful API**: Comprehensive API endpoints with automatic documentation
- **Database Integration**: SQLAlchemy ORM with SQLite/PostgreSQL support
- **CORS Support**: Cross-origin resource sharing for frontend integration
- **Error Handling**: Comprehensive error handling and validation
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation

## Architecture

```
backend/
├── app/
│   ├── api/           # API routes and endpoints
│   ├── core/          # Configuration and settings
│   ├── database/      # Database session management
│   ├── models/        # SQLAlchemy database models
│   ├── schemas/       # Pydantic request/response models
│   └── services/      # Business logic services
├── requirements.txt   # Python dependencies
└── README.md         # This file
```

## Installation

1. **Clone the repository**:
   ```bash
   cd backend
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python -m app.main
   ```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:
- **Interactive API docs**: http://localhost:8000/docs
- **ReDoc documentation**: http://localhost:8000/redoc

## API Endpoints

### Quantum Teleportation
- `POST /api/v1/quantum/teleport` - Perform quantum teleportation
- `GET /api/v1/quantum/circuit/{bit}` - Get circuit visualization
- `POST /api/v1/quantum/simulate` - Simulate teleportation

### Chat Management
- `POST /api/v1/chat/users` - Create user
- `GET /api/v1/chat/users/{user_id}` - Get user
- `PUT /api/v1/chat/users/{user_id}/status` - Update user status
- `GET /api/v1/chat/users/online` - Get online users

### Room Management
- `POST /api/v1/chat/rooms` - Create room
- `GET /api/v1/chat/rooms/{room_id}` - Get room
- `GET /api/v1/chat/users/{user_id}/rooms` - Get user rooms
- `POST /api/v1/chat/rooms/join` - Join room
- `POST /api/v1/chat/rooms/leave` - Leave room

### Message Management
- `POST /api/v1/chat/messages` - Create message
- `GET /api/v1/chat/rooms/{room_id}/messages` - Get room messages
- `GET /api/v1/chat/messages/{message_id}` - Get message

## Quantum Teleportation Protocol

The backend implements the standard quantum teleportation protocol:

1. **State Preparation**: Prepare qubit 0 in the classical bit state (0 or 1)
2. **Bell Pair Creation**: Create entanglement between qubits 1 and 2
3. **Bell Measurement**: Perform Bell measurement on qubits 0 and 1
4. **Conditional Operations**: Apply conditional operations on qubit 2
5. **Final Measurement**: Measure qubit 2 to recover the teleported state

## Configuration

The application uses environment variables for configuration. Create a `.env` file:

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

# Quantum Configuration
QUANTUM_SIMULATOR=qasm_simulator
QUANTUM_SHOTS=1
```

## Database Schema

The application uses SQLAlchemy with the following models:

- **User**: User accounts with online status
- **Room**: Chat rooms with participants
- **RoomParticipant**: Many-to-many relationship between users and rooms
- **Message**: Chat messages with quantum teleportation data

## Development

### Running Tests
```bash
pytest
```

### Code Formatting
```bash
black app/
isort app/
```

### Type Checking
```bash
mypy app/
```

## Production Deployment

1. **Set production environment variables**
2. **Use a production database** (PostgreSQL recommended)
3. **Configure reverse proxy** (nginx)
4. **Use process manager** (systemd, supervisor)
5. **Enable HTTPS** with SSL certificates

## Security Considerations

- Input validation using Pydantic schemas
- SQL injection prevention with SQLAlchemy ORM
- CORS configuration for frontend integration
- Error handling without exposing sensitive information

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License.
