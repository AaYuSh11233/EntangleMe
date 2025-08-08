import { Card } from '../ui/card';
import { ScrollArea } from '../ui/scroll-area';
import { Button } from '../ui/button';
import { Message } from '@/types/chat';
import { api } from '@/api/client';

interface ChatRoomProps {
  messages: Message[];
  currentUser: string;
  isWaiting: boolean;
  onLeave: () => void;
}

export function ChatRoom({ messages, currentUser, isWaiting, onLeave }: ChatRoomProps) {
  const handleSendBit = async (bit: 0 | 1) => {
    try {
      await api.sendBit(currentUser, bit);
    } catch (error) {
      console.error('Error sending bit:', error);
    }
  };

  const handleLeave = async () => {
    try {
      await api.leaveRoom();
      onLeave();
    } catch (error) {
      console.error('Error leaving room:', error);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      <Card className="flex-1 flex flex-col bg-zinc-900 border-zinc-800">
        <div className="p-4 border-b border-zinc-800">
          <div className="flex justify-between items-center">
            <div>
              <h2 className="text-xl font-semibold text-white">Room: Entangle Room</h2>
              <p className="text-sm text-zinc-400">
                Logged in as: {currentUser}
              </p>
            </div>
            <Button 
              variant="destructive" 
              onClick={handleLeave}
              className="bg-red-600 hover:bg-red-700"
            >
              Leave Room
            </Button>
          </div>
        </div>

        <ScrollArea className="flex-1 p-4">
          {isWaiting ? (
            <div className="flex flex-col items-center justify-center h-full space-y-4">
              <div className="text-xl font-semibold text-zinc-400">
                Waiting for another user to join...
              </div>
              <div className="text-sm text-zinc-500">
                Share this link with someone to join:
              </div>
              <div className="font-mono text-sm text-blue-400 bg-zinc-800 px-4 py-2 rounded">
                {window.location.href}
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex gap-2 text-sm ${
                    message.sender === currentUser
                      ? "text-blue-400"
                      : "text-green-400"
                  }`}
                >
                  <span>▸</span>
                  <span>
                    {message.sender} {message.sender === currentUser ? "sent" : "received"} {message.bit}{" "}
                    <span className="text-zinc-500">({message.timestamp})</span>
                  </span>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>

        <div className="p-4 border-t border-zinc-800 flex gap-4">
          <Button 
            className="flex-1 bg-blue-600 hover:bg-blue-700" 
            onClick={() => handleSendBit(0)}
            disabled={isWaiting}
          >
            Send 0
          </Button>
          <Button 
            className="flex-1 bg-blue-600 hover:bg-blue-700" 
            onClick={() => handleSendBit(1)}
            disabled={isWaiting}
          >
            Send 1
          </Button>
        </div>
      </Card>
    </div>
  );
} 