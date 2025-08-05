import { ScrollArea } from '../ui/scroll-area';
import { Separator } from '../ui/separator';
import { Room } from '@/types/chat';
import { useEffect, useState } from 'react';
import { api } from '@/api/client';

export function Sidebar() {
  return (
    <div className="hidden border-r bg-gray-100/40 lg:block dark:bg-gray-800/40">
      <div className="flex h-full w-60 flex-col">
        <div className="p-4">
          <h2 className="mb-2 px-2 text-lg font-semibold tracking-tight">
            Quantum Rooms
          </h2>
        </div>
      </div>
    </div>
  );
} 