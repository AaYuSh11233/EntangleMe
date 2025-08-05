import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
import { Input } from "../ui/input";
import { Button } from "../ui/button";
import { toast } from "sonner";

interface UserNameDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (username: string) => void;
}

export function UserNameDialog({ isOpen, onClose, onSubmit }: UserNameDialogProps) {
  const [username, setUsername] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (username.trim().length < 3) {
      toast.error("Username must be at least 3 characters long");
      return;
    }
    onSubmit(username.trim());
    setUsername(""); // Reset form
    onClose(); // Close dialog after successful submission
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
              autoFocus
            />
          </div>
          <Button type="submit" className="w-full bg-blue-600 hover:bg-blue-700">
            Start Chatting
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  );
} 