import { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { LandingPage } from './components/LandingPage';
import { ChatScreen } from './components/chat/ChatScreen';
import { NotFound } from './components/NotFound';
import { Toaster } from './components/ui/sonner';

function AppContent() {
  const navigate = useNavigate();
  const [username, setUsername] = useState<string | null>(() => {
    return localStorage.getItem('username');
  });

  const handleGetStarted = (name: string) => {
    localStorage.setItem('username', name);
    setUsername(name);
    navigate('/chat');
  };

  const handleLogout = () => {
    localStorage.removeItem('username');
    setUsername(null);
    navigate('/');
  };

  return (
    <>
      <Routes>
        <Route 
          path="/" 
          element={<LandingPage onGetStarted={handleGetStarted} />}
        />
        <Route 
          path="/chat" 
          element={
            username ? (
              <ChatScreen initialUsername={username} onLogout={handleLogout} />
            ) : (
              <Navigate to="/" replace />
            )
          } 
        />
        <Route path="*" element={<NotFound />} />
      </Routes>
      <Toaster />
    </>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AppContent />
    </BrowserRouter>
  );
}

export default App;
