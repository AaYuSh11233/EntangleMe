import { QubitState, TeleportationResult } from '../types/quantum';
import { Room, Message } from '../types/chat';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  // Quantum Operations
  async teleport(state: QubitState): Promise<TeleportationResult> {
    return this.request<TeleportationResult>('/teleport', {
      method: 'POST',
      body: JSON.stringify({ state }),
    });
  }

  // Room Operations
  async getRooms(): Promise<Room[]> {
    return this.request<Room[]>('/rooms');
  }

  async createRoom(name: string): Promise<Room> {
    return this.request<Room>('/rooms/create', {
      method: 'POST',
      body: JSON.stringify({ name }),
    });
  }

  async getRoom(roomId: string): Promise<Room> {
    return this.request<Room>(`/rooms/${roomId}`);
  }

  // Message Operations
  async getRoomMessages(roomId: string): Promise<Message[]> {
    return this.request<Message[]>(`/rooms/${roomId}/messages`);
  }

  async sendMessage(roomId: string, message: Omit<Message, 'id' | 'status'>): Promise<Message> {
    return this.request<Message>(`/rooms/${roomId}/messages`, {
      method: 'POST',
      body: JSON.stringify(message),
    });
  }
}

export const api = new ApiClient(); 