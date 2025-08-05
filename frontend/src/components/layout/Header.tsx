import { Button } from "../ui/button";
import { LogOut } from "lucide-react";

interface HeaderProps {
  onLogout: () => void;
}

export function Header({ onLogout }: HeaderProps) {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center justify-between">
        <div className="mr-4 flex">
          <a className="flex items-center space-x-2" href="/">
            <span className="font-bold">🌀 EntangleMe</span>
          </a>
        </div>
        <div className="flex items-center gap-4">
          <Button 
            variant="ghost" 
            size="icon"
            onClick={onLogout}
            className="text-muted-foreground hover:text-foreground"
          >
            <LogOut className="h-5 w-5" />
          </Button>
        </div>
      </div>
    </header>
  );
} 