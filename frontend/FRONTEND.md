# EntangleMe Frontend Documentation 🌀

## Tech Stack
- React + TypeScript (optional, aligns with PRD's "optionally React")
- Vite
- Tailwind CSS
- shadcn/ui components
- WebSocket for real-time updates
- Axios/fetch for REST API (as per PRD)

---

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
│   ├── api/               # API integration (e.g., /join, /send_bit, /messages)
│   ├── types/             # TypeScript types/interfaces
│   └── styles/            # Global styles
```

---

## Core Features

### 1. Chat Interface (Based on PRD Spec)
- **Login Page**
  - Username input
  - Auto-joins hardcoded room `entangle-room`
  - Waits for 2nd user before transitioning

- **Chat Room**
  - Display logged-in username
  - Room name: Entangle Room
  - Buttons to send 0 or 1
  - Realtime chat message log (bit + sender + timestamp)
  - Leave Room button resets state (no persistent storage)

### 2. Quantum Features (Based on PRD's teleportation logic)
- **Quantum State Selection**
  - UI to send either 0 or 1 (simulated qubit state)
  - Integrated with `/teleport` API
  - Shows classical bits + receiver state response

- **Teleportation Visualization**
  - Circuit display (optional)
  - Measurement result viewer
  - Animations representing state change

### 3. Real-time Communication
- WebSocket client connected to backend
  - `message:new` → appends to chat
  - `quantum:teleport` → visual update
  - `user:presence` → toggles presence display

---

## Component Structure

### Layout Components
```typescript
// MainLayout
- Header
- Sidebar (optional)
- Content Area
- Footer

// ChatLayout
- RoomInfo
- MessageList
- SendControls
```

### Quantum Components
```typescript
// QuantumStateSelector
- Radio or button selector for 0/1
- SendButton with feedback
- Display classical bits and result

// QuantumVisualizer
- SVG or canvas circuit visual (optional)
- ClassicalBitsDisplay
- Measurement animation
```

### Chat Components
```typescript
// ChatRoom
- MessageList
- MessageInput
- UserPresence
- RoomHeader

// Message
- Content
- Bit value
- Timestamp
- Sender info
```

---

## API Integration

### Endpoints
```typescript
// User Join
POST /join
  body: { username: string }
  response: { status: "waiting" | "ready", other_user: string }

// Sending Bit
POST /send_bit
  body: { username: string, bit: 0 | 1 }
  response: { success: true }

// Fetching Messages
GET /messages
  response: [{ sender, bit, timestamp }]

// Teleportation
POST /teleport
  body: { state: "0" | "1" }
  response: { classicalBits, receiverState }
```

### WebSocket Events
```typescript
'message:new'       // New message received
'quantum:teleport'  // State teleportation result
'room:update'       // Room status change
'user:presence'     // User joined/left
```

---

## Styling Guidelines

### Theme
- Quantum/cyberpunk-inspired palette
  - Primary: Blues and purples
  - Secondary: Muted grays
  - Accent: Bright neon for bit transitions

- Typography
  - Sans-serif for UI
  - Monospace for quantum state displays

### UX/UI Design
- Responsive and clean UI
- Minimalistic layout
- Transition animations for message sending and teleportation states

---

## Development Guidelines

### State Management
- Local component state (React hooks)
- Context API or Zustand for shared data
- No session or localStorage used (per PRD)

### Performance Optimizations
- Lazy load visual-heavy components (like circuit views)
- Debounce input and button actions
- Poll `/messages` every 2–3 seconds if WebSocket disconnects

### Error Handling
- Validate bit before sending (0 or 1 only)
- Show user-friendly error messages
- Handle lost connections or 2nd user refresh gracefully

---

## Future Enhancements (From PRD Test Scope)
- Multi-qubit state support
- Advanced teleportation circuit customization
- User-selectable avatars
- Sound effects for bit transmission
- Chat export (optional/local only)
