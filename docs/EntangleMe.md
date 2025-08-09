# EntangleMe Frontend Documentation 🌀

## Project Overview

**EntangleMe** is a quantum-inspired chat application that simulates quantum teleportation for secure message transfer. The system allows two users to join a temporary chat room and send classical bits (0 or 1) to each other using quantum teleportation principles implemented with Qiskit.

### Core Concept
The application follows actual quantum teleportation principles:
> **Entangle → Encode → Measure → Send Classical Bits → Apply Corrections**

This is the same foundation used in **quantum internet** and **secure quantum communication**.

---

## 🛠 Complete Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.8+)
- **Quantum Computing**: Qiskit 0.45.0 + Qiskit-Aer 0.12.2
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT with python-jose
- **Real-time**: WebSocket support with python-socketio
- **Deployment**: Render (Cloud Platform)
- **Testing**: pytest + pytest-asyncio

### Frontend
- **Framework**: React 18.2.0 + TypeScript 5.2.2
- **Build Tool**: Vite 4.5.0
- **Styling**: Tailwind CSS 3.4.1 + shadcn/ui components
- **State Management**: React hooks + Context API
- **Routing**: React Router DOM 7.7.1
- **Animations**: Framer Motion 12.23.12
- **Icons**: Lucide React + Tabler Icons
- **Deployment**: Vercel
- **Development**: Hot reload with Vite

### Additional Tools
- **Quantum Circuit Visualization**: Qiskit visualization tools
- **API Documentation**: FastAPI automatic docs (Swagger/ReDoc)
- **Environment Management**: python-dotenv + Vite env
- **Code Quality**: TypeScript strict mode + ESLint

---

## 🏗 Architecture Overview

### System Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Quantum       │
│   (React/TS)    │◄──►│   (FastAPI)     │◄──►│   (Qiskit)      │
│                 │    │                 │    │                 │
│ • Landing Page  │    │ • REST API      │    │ • Teleportation │
│ • Chat Room     │    │ • WebSocket     │    │ • Circuit Gen   │
│ • Quantum Viz   │    │ • Database      │    │ • Simulation    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Data Flow
1. **User Authentication**: Username-based login (no persistent storage)
2. **Room Management**: Fixed room "Entangle Room" for all users
3. **Message Flow**: Classical bit (0/1) → Quantum teleportation → Receiver
4. **Real-time Updates**: Polling-based message updates (2-3 second intervals)

---

## 📁 Project Structure

### Backend Structure
```
backend/
├── app/
│   ├── api/                 # API endpoints
│   │   ├── chat.py         # Chat-related endpoints
│   │   └── quantum.py      # Quantum teleportation endpoints
│   ├── core/               # Core configuration
│   │   └── config.py       # Settings and environment
│   ├── database/           # Database layer
│   │   └── session.py      # SQLAlchemy session management
│   ├── models/             # Database models
│   │   └── database.py     # SQLAlchemy models
│   ├── schemas/            # Pydantic schemas
│   │   ├── chat.py         # Chat-related schemas
│   │   └── quantum.py      # Quantum-related schemas
│   ├── services/           # Business logic
│   │   ├── chat_service.py # Chat management
│   │   └── quantum_service.py # Quantum teleportation
│   └── main.py            # FastAPI application
├── requirements.txt       # Python dependencies
└── run.py               # Application entry point
```

### Frontend Structure
```
frontend/
├── src/
│   ├── components/        # React components
│   │   ├── chat/         # Chat-related components
│   │   │   ├── ChatRoom.tsx
│   │   │   ├── ChatScreen.tsx
│   │   │   └── UserNameDialog.tsx
│   │   ├── quantum/      # Quantum-specific components
│   │   │   └── QuantumVisualizer.tsx
│   │   ├── layout/       # Layout components
│   │   │   └── MainLayout.tsx
│   │   ├── ui/           # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   └── ...       # Other UI components
│   │   ├── LandingPage.tsx
│   │   ├── NotFound.tsx
│   │   └── ThemeProvider.tsx
│   ├── api/              # API integration
│   │   └── client.ts     # API client with polling
│   ├── types/            # TypeScript types
│   │   ├── chat.ts       # Chat-related types
│   │   └── quantum.ts    # Quantum-related types
│   ├── lib/              # Utilities
│   │   └── utils.ts      # Helper functions
│   ├── assets/           # Static assets
│   │   └── animations/   # Lottie animations
│   ├── App.tsx           # Main application component
│   ├── main.tsx          # Application entry point
│   └── index.css         # Global styles
├── package.json          # Node.js dependencies
├── vite.config.ts        # Vite configuration
├── tailwind.config.ts    # Tailwind CSS configuration
└── tsconfig.json         # TypeScript configuration
```

---

## 🔄 Workflow & User Journey

### 1. Application Startup
1. **Frontend**: Vite dev server starts on `localhost:5173`
2. **Backend**: FastAPI server starts on `localhost:8000`
3. **Database**: SQLite database initialized automatically

### 2. User Authentication Flow
```
Landing Page → Username Input → Join Room → Wait for 2nd User → Chat Room
```

1. **Landing Page**: Modern UI with quantum-themed design
2. **Username Dialog**: Modal for username input
3. **Room Join**: Automatic join to "Entangle Room"
4. **Waiting State**: Shows waiting for second user
5. **Chat Room**: Full chat interface when 2 users present

### 3. Message Sending Flow
```
User Input (0/1) → API Call → Quantum Teleportation → Database Storage → Real-time Update
```

1. **Bit Selection**: User clicks "Send 0" or "Send 1"
2. **API Request**: Frontend calls `/api/v1/quantum/teleport`
3. **Quantum Processing**: Backend simulates teleportation with Qiskit
4. **Database Storage**: Message stored with teleportation results
5. **Real-time Update**: Polling updates chat for all users

### 4. Quantum Teleportation Process
```
Input Bit → Circuit Creation → Bell Pair → Measurement → Classical Bits → Correction → Output
```

1. **Circuit Creation**: Qiskit creates 3-qubit teleportation circuit
2. **Bell Pair**: Entanglement between qubits 1 and 2
3. **Bell Measurement**: Measurement on qubits 0 and 1
4. **Classical Bits**: 2 classical bits sent to receiver
5. **Correction**: Conditional operations on qubit 2
6. **Output**: Final measurement recovers teleported state

---

## 🎯 Core Features

### 1. Chat Interface
- **Real-time Messaging**: Polling-based updates every 2-3 seconds
- **Bit Transmission**: Send classical bits (0 or 1) via quantum teleportation
- **User Management**: Username-based authentication (no persistence)
- **Room System**: Fixed "Entangle Room" for all users
- **Message History**: Temporary storage (cleared on refresh)

### 2. Quantum Features
- **Teleportation Simulation**: Real quantum teleportation using Qiskit
- **Circuit Visualization**: Interactive quantum circuit display
- **Measurement Results**: Classical bits and success probability
- **State Tracking**: Complete teleportation process visualization

### 3. User Experience
- **Modern UI**: Clean, quantum-themed design with animations
- **Responsive Design**: Works on desktop and mobile
- **Real-time Updates**: Live message updates and user presence
- **Error Handling**: Graceful error handling and user feedback

---

## 🔌 API Integration

### Core Endpoints

#### Chat Endpoints
```typescript
// User Management
POST /api/v1/chat/users                    // Create user
GET /api/v1/chat/users/{user_id}           // Get user
PUT /api/v1/chat/users/{user_id}/status    // Update user status
GET /api/v1/chat/users/online              // Get online users

// Room Management
GET /api/v1/chat/rooms                     // Get all rooms
POST /api/v1/chat/rooms                    // Create room
GET /api/v1/chat/rooms/{room_id}           // Get room
GET /api/v1/chat/rooms/{room_id}/participants  // Get room participants
DELETE /api/v1/chat/rooms/{room_id}/participants/{user_id}  // Leave room
POST /api/v1/chat/rooms/join               // Join room
POST /api/v1/chat/rooms/leave              // Leave room

// Message Management
POST /api/v1/chat/messages                 // Create message
GET /api/v1/chat/rooms/{room_id}/messages  // Get room messages
GET /api/v1/chat/messages/{message_id}     // Get specific message
```

#### Quantum Endpoints
```typescript
// Quantum Teleportation
POST /api/v1/quantum/teleport              // Perform teleportation
GET /api/v1/quantum/circuit/{bit}          // Get circuit visualization
POST /api/v1/quantum/simulate              // Simulate teleportation
```

### API Client Implementation
- **Base URL**: Configurable via `VITE_API_URL` environment variable
- **Error Handling**: Comprehensive error handling with user feedback
- **Polling**: Automatic polling for real-time updates
- **Type Safety**: Full TypeScript integration

---

## 🎨 UI/UX Design

### Design System
- **Color Palette**: Quantum/cyberpunk-inspired
  - Primary: Blues (#3B82F6, #1D4ED8)
  - Secondary: Purples (#8B5CF6, #7C3AED)
  - Accent: Neon colors for quantum states
  - Background: Dark theme (#0F172A, #1E293B)

- **Typography**:
  - UI: Inter (sans-serif)
  - Code: JetBrains Mono (monospace)
  - Quantum States: Monospace for technical display

### Component Library
- **shadcn/ui**: Modern, accessible components
- **Custom Components**: Quantum-specific visualizations
- **Animations**: Framer Motion for smooth transitions
- **Icons**: Lucide React + Tabler Icons

### User Interface
- **Landing Page**: Hero section with quantum animations
- **Chat Room**: Clean, focused messaging interface
- **Quantum Visualizer**: Interactive circuit diagrams
- **Responsive Design**: Mobile-first approach

---

## 🚀 Development & Deployment

### Local Development
```bash
# Backend Setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python run.py

# Frontend Setup
cd frontend
npm install
npm run dev
```

### Environment Configuration
```env
# Backend (.env)
API_V1_STR=/api/v1
PROJECT_NAME=EntangleME - Quantum Teleportation Chat
HOST=0.0.0.0
PORT=8000
DEBUG=true
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
DATABASE_URL=sqlite:///./entangleme.db
QUANTUM_SIMULATOR=qasm_simulator
QUANTUM_SHOTS=1

# Frontend (.env)
VITE_API_URL=http://localhost:8000/api/v1
```

### Deployment
- **Backend**: Render (Python/FastAPI)
- **Frontend**: Vercel (React/TypeScript)
- **Database**: SQLite (file-based, no external DB required)

---

## 🧪 Testing & Quality Assurance

### Backend Testing
- **Unit Tests**: pytest for quantum service and chat service
- **Integration Tests**: API endpoint testing
- **Quantum Tests**: Teleportation circuit validation

### Frontend Testing
- **Component Testing**: React component testing
- **Integration Testing**: API integration testing
- **E2E Testing**: User journey testing

### Code Quality
- **TypeScript**: Strict mode enabled
- **ESLint**: Code linting and formatting
- **Prettier**: Code formatting
- **Git Hooks**: Pre-commit checks

---

## 🔮 Future Enhancements

### Short-term (Next Sprint)
- [ ] WebSocket implementation for real-time updates
- [ ] Advanced quantum circuit customization
- [ ] User avatars and profiles
- [ ] Sound effects for quantum teleportation

### Medium-term (Next Quarter)
- [ ] Multi-qubit state support
- [ ] Quantum key distribution (QKD)
- [ ] Advanced quantum algorithms
- [ ] Mobile app development

### Long-term (Next Year)
- [ ] Real quantum hardware integration
- [ ] Quantum network support
- [ ] Enterprise features
- [ ] Quantum cryptography

---

## 📚 Resources & Documentation

### Official Documentation
- [Qiskit Documentation](https://qiskit.org/documentation/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [TypeScript Documentation](https://www.typescriptlang.org/docs/)

### Quantum Computing Resources
- [IBM Quantum Lab](https://quantum-computing.ibm.com/)
- [Qiskit Tutorials](https://github.com/qiskit-community/qiskit-community-tutorials)
- [Quantum Teleportation](https://en.wikipedia.org/wiki/Quantum_teleportation)

### Development Resources
- [Vite Documentation](https://vitejs.dev/)
- [Tailwind CSS](https://tailwindcss.com/)
- [shadcn/ui](https://ui.shadcn.com/)
- [Framer Motion](https://www.framer.com/motion/)

---

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Code Standards
- Follow TypeScript best practices
- Use conventional commits
- Write comprehensive tests
- Update documentation

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ + 🧠 + ⚛️ during CQHack25**
