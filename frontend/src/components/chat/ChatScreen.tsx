import { useState, useEffect, useCallback } from "react";
import { MainLayout } from "../layout/MainLayout";
import { ChatRoom } from "./ChatRoom";
import { Message } from "@/types/chat";
import { api } from "@/api/client";
import { toast } from "sonner";

interface ChatScreenProps {
  initialUsername: string;
  onLogout: () => void;
}

export function ChatScreen({ initialUsername, onLogout }: ChatScreenProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isWaiting, setIsWaiting] = useState(true);
  const [otherUser, setOtherUser] = useState<string | undefined>();

  const handleRoomStatusChange = useCallback((status: string) => {
    setIsWaiting(status === 'waiting');
  }, []);

  const handleMessageUpdate = useCallback((newMessages: Message[]) => {
    setMessages(newMessages);
  }, []);

  // Set up room and message handlers
  useEffect(() => {
    const setupRoom = async () => {
      try {
        const joinResult = await api.joinRoom(initialUsername);
        setIsWaiting(joinResult.status === 'waiting');
        setOtherUser(joinResult.other_user);

        // Start polling for updates
        api.startPolling(handleMessageUpdate, handleRoomStatusChange);
      } catch (error) {
        console.error('Error joining room:', error);
        toast.error('Failed to join the room. Please try again.');
      }
    };

    setupRoom();

    return () => {
      api.stopPolling();
    };
  }, [initialUsername]); // Only depend on initialUsername

  return (
    <MainLayout>
      <ChatRoom
        messages={messages}
        currentUser={initialUsername}
        isWaiting={isWaiting}
        otherUser={otherUser}
        onLeave={onLogout}
      />
   </MainLayout>
  );
} 