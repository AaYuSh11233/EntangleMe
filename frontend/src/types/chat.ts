import { QuantumMessage } from './quantum';

export interface Room {
  id: string;
  name: string;
  participants: string[];
  createdAt: number;
  lastActivity: number;
}

export interface Message extends QuantumMessage {
  id: string;
  roomId: string;
  status: 'sending' | 'sent' | 'failed' | 'teleported';
}

export interface User {
  id: string;
  name: string;
  isOnline: boolean;
  lastSeen?: number;
} 