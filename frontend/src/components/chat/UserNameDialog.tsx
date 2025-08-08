import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
import { Input } from "../ui/input";
import { Button } from "../ui/button";
import { toast } from "sonner";

interface UserNameDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onGetStarted: (username: string) => void;
}

export function UserNameDialog({ isOpen, onClose, onGetStarted }: UserNameDialogProps) {
  const [username, setUsername] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (username.trim().length < 3) {
      toast.error("Username must be at least 3 characters long");
      return;
    }

    setIsLoading(true);
    try {
      onGetStarted(username.trim());
      setUsername("");
      onClose();
    } catch (error) {
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