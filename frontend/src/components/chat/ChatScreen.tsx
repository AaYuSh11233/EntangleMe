import { useState, useEffect } from "react";
import { MainLayout } from "../layout/MainLayout";
import { ChatRoom } from "./ChatRoom";
import { Message } from "@/types/chat";
import { api, MockStorage } from "@/api/client";
import { toast } from "sonner";

interface ChatScreenProps {
  initialUsername: string;
  onLogout: () => void;
}

export function ChatScreen({ initialUsername, onLogout }: ChatScreenProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isWaiting, setIsWaiting] = useState(true);

  useEffect(() => {
    const handleRoomStatusChange = () => {
      const userCount = MockStorage.getUserCount();
      setIsWaiting(userCount !== 2);
    };

    const handleMessageUpdate = () => {
      setMessages(MockStorage.getMessages());
    };

    const setupRoom = async () => {
      try {
        await api.joinRoom(initialUsername);
        handleRoomStatusChange(); // Initial status check
        handleMessageUpdate(); // Initial messages

        // Set up event listeners for real-time updates
        window.addEventListener('roomUpdate', handleRoomStatusChange);
        window.addEventListener('messageUpdate', handleMessageUpdate);
      } catch (error) {
        console.error('Error joining room:', error);
        toast.error('Failed to join the room. Please try again.');
      }
    };

    setupRoom();

    return () => {
      api.leaveRoom().catch(console.error);
      window.removeEventListener('roomUpdate', handleRoomStatusChange);
      window.removeEventListener('messageUpdate', handleMessageUpdate);
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