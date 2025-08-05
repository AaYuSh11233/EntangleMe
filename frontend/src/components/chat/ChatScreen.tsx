import { useState } from "react";
import { MainLayout } from "../layout/MainLayout";
import { ChatRoom } from "./ChatRoom";
import { Message, Room } from "@/types/chat";

// Sample room for testing
const defaultRoom: Room = {
  id: "quantum-chat",
  name: "Quantum Chat Room",
  participants: [],
  createdAt: Date.now(),
  lastActivity: Date.now(),
};

interface ChatScreenProps {
  initialUsername: string;
  onLogout: () => void;
}

export function ChatScreen({ initialUsername, onLogout }: ChatScreenProps) {
  const [messages, setMessages] = useState<Message[]>([]);

  const handleNewMessage = (message: Message) => {
    setMessages((prev) => [...prev, message]);
  };

  return (
    <MainLayout onLogout={onLogout}>
      <ChatRoom
        room={{
          ...defaultRoom,
          participants: [...defaultRoom.participants, initialUsername],
        }}
        messages={messages}
        onNewMessage={handleNewMessage}
        currentUser={initialUsername}
      />
    </MainLayout>
  );
} 