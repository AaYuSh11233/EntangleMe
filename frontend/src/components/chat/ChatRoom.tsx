import { useState } from 'react';
import { Card } from '../ui/card';
import { ScrollArea } from '../ui/scroll-area';
import { QuantumStateSelector } from '../quantum/QuantumStateSelector';
import { QuantumVisualizer } from '../quantum/QuantumVisualizer';
import { Message, Room } from '@/types/chat';
import { TeleportationResult } from '@/types/quantum';

interface ChatRoomProps {
  room: Room;
  messages: Message[];
  currentUser: string;
  onNewMessage: (message: Message) => void;
}

export function ChatRoom({ room, messages, currentUser, onNewMessage }: ChatRoomProps) {
  const [lastTeleportation, setLastTeleportation] = useState<TeleportationResult>();

  const handleStateSelected = (state: "0" | "1", result: TeleportationResult) => {
    setLastTeleportation(result);
    
    const newMessage: Message = {
      id: Date.now().toString(),
      roomId: room.id,
      senderId: currentUser,
      receiverId: room.participants.find(p => p !== currentUser) || "all",
      state,
      timestamp: Date.now(),
      status: "teleported",
      result,
    };

    onNewMessage(newMessage);
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      <Card className="flex-1 flex flex-col">
        <div className="p-4 border-b">
          <h2 className="text-xl font-semibold">{room.name}</h2>
          <p className="text-sm text-muted-foreground">
            {room.participants.length} participants
          </p>
        </div>
        <ScrollArea className="flex-1 p-4">
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex flex-col space-y-1 rounded-lg p-3 ${
                  message.senderId === currentUser
                    ? "bg-blue-500/20 ml-auto"
                    : "bg-muted/50"
                } max-w-[80%]`}
              >
                <div className="flex items-center gap-2">
                  <span className="font-medium">{message.senderId}</span>
                  <span className="text-xs text-muted-foreground">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div className="font-mono">
                  Sent state: |{message.state}⟩
                </div>
                {message.result && (
                  <div className="text-sm text-muted-foreground">
                    Classical bits: {message.result.classicalBits}
                    <br />
                    Received: |{message.result.receiverState}⟩
                  </div>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
        <div className="p-4 border-t space-y-4">
          <QuantumStateSelector
            onStateSelected={handleStateSelected}
          />
          {lastTeleportation && (
            <QuantumVisualizer result={lastTeleportation} />
          )}
        </div>
      </Card>
    </div>
  );
} 