import { ReactNode } from 'react';

interface MainLayoutProps {
  children: ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="min-h-screen bg-zinc-950 p-6">
      <main className="container mx-auto">
        {children}
      </main>
    </div>
  );
} 