# 🌀 EntangleMe Frontend

> Quantum Teleportation Chat Application - React/TypeScript Frontend

A modern, responsive frontend for EntangleMe, a quantum-inspired chat application that simulates quantum teleportation for secure message transfer. Built with React, TypeScript, and modern web technologies.

## 🎯 **Project Overview**

EntangleMe Frontend is a React-based web application that provides a user-friendly interface for quantum teleportation chat. Users can join chat rooms, send classical bits (0 or 1) via quantum teleportation, and visualize the quantum processes in real-time.

### **Core Features**
- 🎨 **Modern UI/UX**: Clean, quantum-themed design with animations
- ⚛️ **Quantum Visualization**: Interactive quantum circuit diagrams
- 💬 **Real-time Chat**: Live messaging with quantum teleportation
- 🔄 **Real-time Updates**: Polling-based message updates
- 📱 **Responsive Design**: Works on desktop and mobile
- 🎯 **Type Safety**: Full TypeScript integration

## 🛠 **Tech Stack**

### **Core Framework**
- **React 18.2.0** - Modern React with hooks and concurrent features
- **TypeScript 5.2.2** - Type-safe JavaScript
- **Vite 4.5.0** - Fast build tool and dev server

### **Styling & UI**
- **Tailwind CSS 3.4.1** - Utility-first CSS framework
- **shadcn/ui** - Modern, accessible component library
- **Framer Motion 12.23.12** - Smooth animations and transitions
- **Lucide React** - Beautiful icons
- **Tabler Icons** - Additional icon set

### **State Management & Routing**
- **React Router DOM 7.7.1** - Client-side routing
- **React Hooks** - Local state management
- **Context API** - Shared state management

### **Development Tools**
- **ESLint** - Code linting
- **Prettier** - Code formatting
- **TypeScript** - Static type checking
- **Vite** - Hot module replacement

## 📁 **Project Structure**

```
frontend/
├── src/
│   ├── components/           # React components
│   │   ├── chat/            # Chat-related components
│   │   │   ├── ChatRoom.tsx
│   │   │   ├── ChatScreen.tsx
│   │   │   └── UserNameDialog.tsx
│   │   ├── quantum/         # Quantum-specific components
│   │   │   └── QuantumVisualizer.tsx
│   │   ├── layout/          # Layout components
│   │   │   └── MainLayout.tsx
│   │   ├── ui/              # shadcn/ui components
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   └── ...          # Other UI components
│   │   ├── LandingPage.tsx
│   │   ├── NotFound.tsx
│   │   └── ThemeProvider.tsx
│   ├── api/                 # API integration
│   │   └── client.ts        # API client with polling
│   ├── types/               # TypeScript types
│   │   ├── chat.ts          # Chat-related types
│   │   └── quantum.ts       # Quantum-related types
│   ├── lib/                 # Utilities
│   │   └── utils.ts         # Helper functions
│   ├── assets/              # Static assets
│   │   └── animations/      # Lottie animations
│   ├── App.tsx              # Main application component
│   ├── main.tsx             # Application entry point
│   └── index.css            # Global styles
├── package.json             # Dependencies and scripts
├── vite.config.ts           # Vite configuration
├── tailwind.config.ts       # Tailwind CSS configuration
├── tsconfig.json            # TypeScript configuration
└── README.md                # This file
```

## 🚀 **Quick Start**

### **Prerequisites**
- Node.js 16+ 
- npm or yarn
- Git

### **Installation**

1. **Clone the repository**
   ```bash
   git clone https://github.com/dev-Ninjaa/EntangleMe.git
   cd EntangleMe/frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your backend URL
   VITE_API_URL=http://localhost:8000/api/v1
   ```

4. **Start development server**
   ```bash
   npm run dev
   # or
   yarn dev
   ```

5. **Open your browser**
   ```
   http://localhost:5173
   ```

## 🎨 **Features & Components**

### **Landing Page**
- Modern quantum-themed design
- Username input modal
- Automatic room joining
- Responsive layout

### **Chat Room**
- Real-time message updates (polling every 2-3 seconds)
- Bit transmission buttons (0/1)
- Quantum visualization integration
- User presence indicators

### **Quantum Visualization**
- Interactive circuit diagrams
- Step-by-step teleportation process
- Measurement results display
- Success probability visualization

### **User Experience**
- Clean, modern interface
- Smooth animations and transitions
- Error handling and user feedback
- Mobile-responsive design

## 🔌 **API Integration**

### **Core Endpoints**

The frontend integrates with the backend API through the `api/client.ts` module:

```typescript
// User Management
POST /api/v1/chat/users                    // Create user
GET /api/v1/chat/users/{user_id}           // Get user
PUT /api/v1/chat/users/{user_id}/status    // Update user status

// Room Management
GET /api/v1/chat/rooms                     // Get all rooms
POST /api/v1/chat/rooms                    // Create room
GET /api/v1/chat/rooms/{room_id}           // Get room
POST /api/v1/chat/rooms/join               // Join room
POST /api/v1/chat/rooms/leave              // Leave room

// Message Management
POST /api/v1/chat/messages                 // Create message
GET /api/v1/chat/rooms/{room_id}/messages  // Get room messages

// Quantum Teleportation
POST /api/v1/quantum/teleport              // Perform teleportation
GET /api/v1/quantum/circuit/{bit}          // Get circuit visualization
```

### **Real-time Updates**
- Polling-based updates every 2-3 seconds
- Automatic reconnection on network issues
- Real-time message synchronization

## 🎯 **Development**

### **Available Scripts**

```bash
# Development
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build

# Code Quality
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript type checking
```

### **Development Guidelines**

1. **TypeScript**: Use strict mode and proper typing
2. **Components**: Follow functional component patterns with hooks
3. **Styling**: Use Tailwind CSS classes and shadcn/ui components
4. **State Management**: Use React hooks and Context API
5. **Error Handling**: Implement proper error boundaries and user feedback

### **Code Structure**

- **Components**: Functional components with TypeScript
- **Hooks**: Custom hooks for reusable logic
- **Types**: TypeScript interfaces and types
- **Utils**: Helper functions and utilities
- **API**: API client and integration

## 🎨 **Design System**

### **Color Palette**
- **Primary**: Blues (#3B82F6, #1D4ED8)
- **Secondary**: Purples (#8B5CF6, #7C3AED)
- **Accent**: Neon colors for quantum states
- **Background**: Dark theme (#0F172A, #1E293B)

### **Typography**
- **UI**: Inter (sans-serif)
- **Code**: JetBrains Mono (monospace)
- **Quantum States**: Monospace for technical display

### **Components**
- **shadcn/ui**: Modern, accessible components
- **Custom Components**: Quantum-specific visualizations
- **Animations**: Framer Motion for smooth transitions

## 🧪 **Testing**

### **Component Testing**
```bash
# Run component tests
npm run test

# Run tests in watch mode
npm run test:watch
```

### **Integration Testing**
- API integration testing
- User journey testing
- Quantum simulation testing

## 🚀 **Deployment**

### **Production Build**
```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### **Deployment Platforms**
- **Vercel**: Recommended for React applications
- **Netlify**: Alternative deployment option
- **GitHub Pages**: Static site hosting

### **Environment Variables**
```env
# Production
VITE_API_URL=https://your-backend-url.com/api/v1
```

## 🔧 **Configuration**

### **Vite Configuration**
```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: true
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
})
```

### **Tailwind Configuration**
```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Custom quantum theme colors
      }
    },
  },
  plugins: [],
} satisfies Config
```

## 🤝 **Contributing**

### **Development Workflow**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### **Code Standards**
- Follow TypeScript best practices
- Use conventional commits
- Write comprehensive tests
- Update documentation


**For more information, visit the main project repository: [EntangleMe](https://github.com/dev-Ninjaa/EntangleMe)** 