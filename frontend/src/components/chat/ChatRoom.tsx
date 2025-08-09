import { Card } from '../ui/card';
import { ScrollArea } from '../ui/scroll-area';
import { Button } from '../ui/button';
import { Message } from '@/types/chat';
import { TeleportationResult } from '@/types/quantum';
import { api } from '@/api/client';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';
import { useState } from 'react';
import { QuantumVisualizer } from '../quantum/QuantumVisualizer';

interface ChatRoomProps {
  messages: Message[];
  currentUser: string;
  isWaiting: boolean;
  otherUser?: string;
  onLeave: () => void;
}

export function ChatRoom({ messages, currentUser, isWaiting, otherUser, onLeave }: ChatRoomProps) {
  const [isSending, setIsSending] = useState(false);
  const [lastTeleportationResult, setLastTeleportationResult] = useState<TeleportationResult | null>(null);

  const handleSendBit = async (bit: 0 | 1) => {
    if (isSending) return;
    
    setIsSending(true);
    try {
      const result = await api.sendBit(currentUser, bit);
      
      if (result.success) {
        toast.success(`Successfully teleported bit ${bit}!`);
        if (result.teleportation_result) {
          setLastTeleportationResult(result.teleportation_result);
          console.log('Teleportation result:', result.teleportation_result);
        }
      } else {
        toast.error('Failed to teleport bit');
      }
    } catch (error) {
      console.error('Error sending bit:', error);
      toast.error('Failed to send bit. Please try again.');
    } finally {
      setIsSending(false);
    }
  };

  const handleLeave = async () => {
    try {
      await api.leaveRoom();
      onLeave();
    } catch (error) {
      console.error('Error leaving room:', error);
      onLeave(); // Still leave even if API call fails
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)]">
      <Card className="flex-1 flex flex-col bg-zinc-900 border-zinc-800">
        <div className="p-4 border-b border-zinc-800 bg-gradient-to-r from-zinc-900 to-zinc-800">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-blue-500/20 flex items-center justify-center backdrop-blur-sm">
                🌀
              </div>
              <div>
                <h2 className="text-xl font-bold text-white flex items-center gap-2">
                  Entangle Room
                  <span className={cn(
                    "px-2 py-1 rounded-full text-xs font-medium",
                    isWaiting 
                      ? "bg-yellow-500/20 text-yellow-400" 
                      : "bg-green-500/20 text-green-400"
                  )}>
                    {isWaiting ? 'Waiting' : 'Connected'}
                  </span>
                </h2>
                <p className="text-sm text-zinc-400">
                  Logged in as <span className="text-blue-400">{currentUser}</span>
                  {otherUser && (
                    <span className="ml-2">
                      • Connected with <span className="text-purple-400">{otherUser}</span>
                    </span>
                  )}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {lastTeleportationResult && (
                <QuantumVisualizer 
                  teleportationResult={lastTeleportationResult}
                  bit={lastTeleportationResult.sent_bit as 0 | 1}
                />
              )}
              <Button 
                variant="ghost"
                onClick={handleLeave}
                className="text-zinc-400 hover:text-red-400 hover:bg-red-500/10"
              >
                <motion.div
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  Leave Room
                </motion.div>
              </Button>
            </div>
          </div>
        </div>

        <ScrollArea className="flex-1 p-4">
          {isWaiting ? (
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="flex flex-col items-center justify-center h-full space-y-4"
            >
              <div className="text-xl font-semibold text-zinc-400">
                Waiting for another user to join...
              </div>
              <div className="text-sm text-zinc-500">
                Share this link with someone to join:
              </div>
              <div className="font-mono text-sm text-blue-400 bg-zinc-800 px-4 py-2 rounded">
                {window.location.href}
              </div>
            </motion.div>
          ) : (
            <div className="space-y-4 py-4">
              <AnimatePresence>
                {messages.map((message, index) => {
                  const isCurrentUser = message.sender === currentUser;
                  return (
                    <motion.div
                      key={`${message.sender}-${message.timestamp}-${index}`}
                      initial={{ opacity: 0, y: 20 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0 }}
                      className={cn(
                        "flex w-full mb-4",
                        isCurrentUser ? "justify-end" : "justify-start"
                      )}
                    >
                      <div
                        className={cn(
                          "flex flex-col max-w-[80%] rounded-lg px-4 py-2",
                          isCurrentUser
                            ? "bg-blue-600 text-white items-end rounded-br-none"
                            : "bg-zinc-800 text-white items-start rounded-bl-none"
                        )}
                      >
                        <div className="text-sm font-medium mb-1">
                          {isCurrentUser ? "You" : message.sender}
                        </div>
                        <div className="text-lg font-semibold mb-1">
                          {message.bit}
                        </div>
                        {message.teleportation_result && (
                          <div className="text-xs text-zinc-300/60 mb-1">
                            📡 Teleported via quantum entanglement
                          </div>
                        )}
                        <div className="text-xs text-zinc-300/80">
                          {message.timestamp}
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </AnimatePresence>
            </div>
          )}
        </ScrollArea>

        <div className="p-4 border-t border-zinc-800">
          <div className="grid grid-cols-2 gap-4 max-w-md mx-auto">
            <Button 
              className={cn(
                "h-16 text-lg font-semibold transition-all duration-200",
                "bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-500 hover:to-blue-600",
                "disabled:from-zinc-700 disabled:to-zinc-800 disabled:opacity-50"
              )}
              onClick={() => handleSendBit(0)}
              disabled={isWaiting || isSending}
            >
              <motion.div
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
              >
                {isSending ? "Teleporting..." : "Send 0"}
              </motion.div>
            </Button>
            <Button 
              className={cn(
                "h-16 text-lg font-semibold transition-all duration-200",
                "bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-500 hover:to-purple-600",
                "disabled:from-zinc-700 disabled:to-zinc-800 disabled:opacity-50"
              )}
              onClick={() => handleSendBit(1)}
              disabled={isWaiting || isSending}
            >
              <motion.div
                whileHover={{ scale: 1.1 }}
                whileTap={{ scale: 0.95 }}
              >
                {isSending ? "Teleporting..." : "Send 1"}
              </motion.div>
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
} 
