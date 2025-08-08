import { useState, useEffect } from "react";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "../ui/dialog";
import { Input } from "../ui/input";
import { Button } from "../ui/button";
import { toast } from "sonner";
import { MockStorage } from "../../api/client";

interface UserNameDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onGetStarted: (username: string) => void;
}

export function UserNameDialog({ isOpen, onClose, onGetStarted }: UserNameDialogProps) {
  const [username, setUsername] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  // Reset the form when dialog is opened/closed
  useEffect(() => {
    if (isOpen) {
      setUsername("");
      setIsLoading(false);
    }
  }, [isOpen]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedUsername = username.trim();
    if (trimmedUsername.length < 3) {
      toast.error("Username must be at least 3 characters long");
      return;
    }

    // Check if username is already taken
    const userCount = MockStorage.getUserCount();
    if (userCount >= 2) {
      toast.error("The room is full. Please try again later.");
      return;
    }
    
    const otherUser = MockStorage.getOtherUser("");
    if (otherUser === trimmedUsername) {
      toast.error("This username is already taken. Please choose another.");
      return;
    }

    setIsLoading(true);
    try {
      onGetStarted(trimmedUsername);
      setUsername("");
      onClose();
    } catch (error) {
      console.error('Error in handleSubmit:', error);
      toast.error("Failed to join the room. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[425px] bg-zinc-900 border-zinc-800">
        <DialogHeader>
          <DialogTitle className="text-lg text-white">Welcome to EntangleMe</DialogTitle>
          <DialogDescription className="text-zinc-400">
            Enter your name to join the quantum chat experience. Names must be unique and at least 3 characters long.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-6 pt-4">
          <div className="space-y-2">
            <Input
              id="username"
              placeholder="Enter your name"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full bg-zinc-800 border-zinc-700 text-white"
              disabled={isLoading}
              autoFocus
              aria-label="Username input"
            />
          </div>
          <Button 
            type="submit" 
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
            disabled={isLoading}
          >
            Join Room
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
} 