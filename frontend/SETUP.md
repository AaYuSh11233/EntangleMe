# 🌀 EntangleMe Frontend Setup Guide

> Complete setup guide for the EntangleMe React/TypeScript frontend

This guide will help you set up and run the EntangleMe frontend application locally for development.

## 📋 **Prerequisites**

### **Required Software**
- **Node.js 16+** - [Download here](https://nodejs.org/)
- **npm or yarn** - Package managers
- **Git** - Version control
- **Modern browser** - Chrome, Firefox, Safari, or Edge

### **System Requirements**
- **OS**: Windows 10+, macOS 10.15+, or Linux
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 2GB free space
- **Network**: Internet connection for package installation

## 🚀 **Quick Setup**

### **Step 1: Clone the Repository**
```bash
# Clone the main repository
git clone https://github.com/dev-Ninjaa/EntangleMe.git

# Navigate to frontend directory
cd EntangleMe/frontend
```

### **Step 2: Install Dependencies**
```bash
# Using npm (recommended)
npm install

# Or using yarn
yarn install
```

### **Step 3: Environment Configuration**
```bash
# Copy environment template
cp .env.example .env

# Edit the .env file with your backend URL
# For local development:
VITE_API_URL=http://localhost:8000/api/v1
```

### **Step 4: Start Development Server**
```bash
# Start development server
npm run dev

# Or using yarn
yarn dev
```

### **Step 5: Open in Browser**
```
http://localhost:5173
```

## 🔧 **Detailed Setup**

### **Environment Variables**

Create a `.env` file in the frontend directory:

```env
# API Configuration
VITE_API_URL=http://localhost:8000/api/v1

# Development Configuration
VITE_DEV_MODE=true
VITE_DEBUG=true

# Optional: Custom port
VITE_PORT=5173
```

### **Backend Integration**

The frontend requires a running backend server. Make sure:

1. **Backend is running** on `http://localhost:8000`
2. **API endpoints** are accessible
3. **CORS** is configured properly

### **Database Setup**

The frontend doesn't require direct database access, but the backend needs:

- **SQLite** database (auto-created)
- **Proper permissions** for database access

## 🎯 **Development Workflow**

### **Available Scripts**

```bash
# Development
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build

# Code Quality
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript type checking
npm run format       # Format code with Prettier

# Testing (if configured)
npm run test         # Run tests
npm run test:watch   # Run tests in watch mode
```

### **Development Server**

The development server runs on `http://localhost:5173` by default and includes:

- **Hot Module Replacement** - Instant code updates
- **TypeScript compilation** - Real-time type checking
- **Error overlay** - Clear error messages
- **Source maps** - Debug-friendly code

### **Code Structure**

```
src/
├── components/           # React components
│   ├── chat/            # Chat-related components
│   ├── quantum/         # Quantum-specific components
│   ├── layout/          # Layout components
│   └── ui/              # shadcn/ui components
├── api/                 # API integration
├── types/               # TypeScript types
├── lib/                 # Utilities
└── assets/              # Static assets
```

## 🎨 **Styling & UI**

### **Tailwind CSS**

The project uses Tailwind CSS for styling:

```bash
# Tailwind configuration
tailwind.config.ts

# Custom styles
src/index.css
```

### **shadcn/ui Components**

Modern, accessible components from shadcn/ui:

```bash
# Install new components
npx shadcn-ui@latest add [component-name]

# Available components
- button
- card
- dialog
- input
- form
- and more...
```

### **Custom Components**

Quantum-specific components in `src/components/quantum/`:

- `QuantumVisualizer.tsx` - Circuit visualization
- Custom quantum-themed components

## 🔌 **API Integration**

### **API Client**

The frontend uses a custom API client in `src/api/client.ts`:

```typescript
// Example usage
import { api } from '@/api/client'

// Join room
const result = await api.joinRoom(username)

// Send bit
const response = await api.sendBit(username, 1)

// Get messages
const messages = await api.getMessages()
```

### **Real-time Updates**

Polling-based updates every 2-3 seconds:

```typescript
// Start polling
api.startPolling(handleMessageUpdate, handleRoomStatusChange)

// Stop polling
api.stopPolling()
```

## 🧪 **Testing**

### **Component Testing**

```bash
# Run tests
npm run test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

### **Integration Testing**

Test API integration and user journeys:

```bash
# Run integration tests
npm run test:integration
```

## 🚀 **Production Build**

### **Build Process**

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### **Build Output**

The build creates a `dist/` directory with:

- **Static assets** - HTML, CSS, JS
- **Optimized bundles** - Minified and compressed
- **Source maps** - For debugging

### **Deployment**

#### **Vercel (Recommended)**
```bash
# Install Vercel CLI
npm i -g vercel

# Deploy
vercel
```

#### **Netlify**
```bash
# Build and deploy
npm run build
# Upload dist/ folder to Netlify
```

#### **GitHub Pages**
```bash
# Build
npm run build

# Deploy to GitHub Pages
# Configure in repository settings
```

## 🔧 **Configuration**

### **Vite Configuration**

```typescript
// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})
```

### **TypeScript Configuration**

```json
// tsconfig.json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
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
        quantum: {
          primary: '#3B82F6',
          secondary: '#8B5CF6',
          accent: '#06B6D4',
        },
      },
      animation: {
        'quantum-pulse': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
    },
  },
  plugins: [],
} satisfies Config
```

## 🐛 **Troubleshooting**

### **Common Issues**

#### **Port Already in Use**
```bash
# Kill process on port 5173
npx kill-port 5173

# Or use different port
npm run dev -- --port 3000
```

#### **Dependencies Issues**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

#### **TypeScript Errors**
```bash
# Check TypeScript configuration
npx tsc --noEmit

# Fix type issues
npm run type-check
```

#### **API Connection Issues**
```bash
# Check backend is running
curl http://localhost:8000/health

# Check CORS configuration
# Ensure backend allows frontend origin
```

### **Development Tools**

#### **React Developer Tools**
- Install [React Developer Tools](https://chrome.google.com/webstore/detail/react-developer-tools/fmkadmapgofadopljbjfkapdkoienihi) browser extension

#### **Redux DevTools** (if using Redux)
- Install [Redux DevTools](https://chrome.google.com/webstore/detail/redux-devtools/lmhkpmbekcpmknklioeibfkpmmfibljd) browser extension


## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](https://github.com/dev-Ninjaa/EntangleMe?tab=License-1-ov-file) file for details.

---

**Happy coding! 🌀⚛️** 