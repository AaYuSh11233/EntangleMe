import { ReactNode } from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';

interface MainLayoutProps {
  children: ReactNode;
  onLogout: () => void;
}

export function MainLayout({ children, onLogout }: MainLayoutProps) {
  return (
    <div className="min-h-screen bg-background">
      <Header onLogout={onLogout} />
      <div className="flex">
        <Sidebar />
        <main className="flex-1 p-6">
          {children}
        </main>
      </div>
    </div>
  );
} 