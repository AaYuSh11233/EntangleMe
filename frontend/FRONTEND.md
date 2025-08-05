# EntangleMe Frontend Documentation 🌀

## Tech Stack
- React + TypeScript
- Vite
- Tailwind CSS
- shadcn/ui components
- WebSocket for real-time updates

## Project Structure
```
frontend/
├── src/
│   ├── components/         # Reusable UI components
│   │   ├── ui/            # shadcn/ui components
│   │   ├── layout/        # Layout components
│   │   ├── quantum/       # Quantum-specific components
│   │   └── chat/          # Chat-related components
│   ├── lib/               # Utilities and helpers
│   ├── hooks/             # Custom React hooks
│   ├── api/               # API integration
│   ├── types/             # TypeScript types/interfaces
│   └── styles/            # Global styles
```

## Core Features

### 1. Chat Interface
- **Room List**
  - Display active chat rooms
  - Create new room functionality
  - Room status indicators

- **Chat Room**
  - Message history display
  - Message input with quantum state selector
  - Real-time message updates
  - User presence indicators

### 2. Quantum Features
- **State Management**
  - Qubit state selection (0/1)
  - Teleportation status visualization
  - Classical bits display
  - Measurement results view

- **Visualization**
  - Quantum circuit representation
  - Teleportation animation
  - State transition effects

### 3. Real-time Communication
- WebSocket connection for:
  - Instant message updates
  - Room status changes
  - Quantum state broadcasts
  - User presence tracking

## Component Structure

### Layout Components
```typescript
// MainLayout
- Header
- Sidebar
- Content Area
- Footer

// ChatLayout
- RoomList
- ChatArea
- UserList
```

### Quantum Components
```typescript
// QuantumStateSelector
- StateInput (0/1)
- SendButton
- TeleportationStatus

// QuantumVisualizer
- CircuitDisplay
- MeasurementResults
- ClassicalBitsDisplay
```

### Chat Components
```typescript
// ChatRoom
- MessageList
- MessageInput
- UserPresence
- RoomInfo

// Message
- Content
- Timestamp
- QuantumState
- SenderInfo
```

## API Integration

### Endpoints
```typescript
// Quantum Operations
POST /teleport
  body: { state: "0" | "1" }
  response: {
    classicalBits: string,
    receiverState: string
  }

// Room Operations
GET /rooms
POST /rooms/create
GET /rooms/:id

// Messages
GET /rooms/:id/messages
POST /rooms/:id/messages
```

### WebSocket Events
```typescript
// Events
'message:new'       // New message received
'quantum:teleport'  // Quantum state teleported
'room:update'       // Room status changed
'user:presence'     // User presence update
```

## Styling Guidelines

### Theme
- Color Palette
  - Primary: Quantum-inspired blues/purples
  - Secondary: Modern grays
  - Accent: Bright highlights for quantum states

- Typography
  - Main: System fonts for performance
  - Monospace: For quantum states/measurements

### Component Design
- Minimalist, clean interfaces
- Responsive layouts
- Smooth transitions
- Clear visual hierarchy

## Development Guidelines

### State Management
- React hooks for local state
- Context for shared state
- WebSocket for real-time updates

### Performance
- Code splitting for routes
- Lazy loading for heavy components
- Memoization for expensive calculations
- Optimized re-renders

### Error Handling
- Graceful fallbacks
- User-friendly error messages
- Retry mechanisms for failed operations

## Future Enhancements
- Multiple qubit states
- Advanced quantum visualizations
- Circuit customization
- Message encryption
- Performance metrics 