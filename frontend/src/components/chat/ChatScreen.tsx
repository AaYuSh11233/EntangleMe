import { useState, useEffect } from "react";
import { MainLayout } from "../layout/MainLayout";
import { ChatRoom } from "./ChatRoom";
import { Message } from "@/types/chat";
import { api } from "@/api/client";

interface ChatScreenProps {
  initialUsername: string;
  onLogout: () => void;
}

export function ChatScreen({ initialUsername, onLogout }: ChatScreenProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isWaiting, setIsWaiting] = useState(true);

  useEffect(() => {
    const handleRoomStatusChange = (event: CustomEvent<{ status: 'waiting' | 'ready', other_user?: string }>) => {
      setIsWaiting(event.detail.status === 'waiting');
    };

    const setupRoom = async () => {
      try {
        const response = await api.joinRoom(initialUsername);
        setIsWaiting(response.status === 'waiting');
        
        // Start listening for messages and room status changes
        api.startPolling((newMessages) => {
          setMessages(newMessages);
        });

        // Listen for room status changes
        window.addEventListener('roomStatusChange', handleRoomStatusChange as EventListener);
      } catch (error) {
        console.error('Error joining room:', error);
      }
    };

    setupRoom();

    return () => {
      api.stopPolling();
      window.removeEventListener('roomStatusChange', handleRoomStatusChange as EventListener);
    };
  }, [initialUsername]);

  return (
    <MainLayout>
      <ChatRoom
        messages={messages}
        currentUser={initialUsername}
        isWaiting={isWaiting}
        onLeave={onLogout}
      />
    </MainLayout>
  );
} 