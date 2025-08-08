export interface Room {
  name: string;
  users: string[];
  status: 'waiting' | 'ready';
}

export interface Message {
  sender: string;
  bit: 0 | 1;
  timestamp: string;
}

export interface JoinResponse {
  status: 'waiting' | 'ready';
  other_user?: string;
}

export interface SendBitResponse {
  success: boolean;
}

export interface User {
  username: string;
} 