import { JoinResponse, Message, SendBitResponse } from '../types/chat';

// Fast in-memory storage with broadcast
export class MockStorage {
  private static users: Set<string> = new Set();
  private static messages: Message[] = [];
  private static channel = new BroadcastChannel('entangleme');
  private static readonly STORAGE_KEY = 'entangleme_state';
  
  static {
    // Initialize from storage if available
    try {
      const savedState = localStorage.getItem(this.STORAGE_KEY);
      if (savedState) {
        const { users, messages } = JSON.parse(savedState);
        this.users = new Set(users);
        this.messages = messages;
      }
    } catch (error) {
      console.error('Error loading saved state:', error);
    }

    // Set up channel listener
    this.setupChannelListener();
  }
  
  private static saveState() {
    const state = {
      users: Array.from(this.users),
      messages: this.messages
    };
    localStorage.setItem(this.STORAGE_KEY, JSON.stringify(state));
  }

  static addMessage(message: Message) {
    this.messages.push(message);
    this.saveState();
    this.channel.postMessage({ type: 'NEW_MESSAGE', data: message });
  }
  
  static getMessages(): Message[] {
    return [...this.messages];
  }
  
  static addUser(username: string) {
    // Remove any old instances of this user first
    this.users.delete(username);
    this.users.add(username);
    this.saveState();
    this.channel.postMessage({ type: 'ADD_USER', data: username });
  }
  
  static removeUser(username: string) {
    this.users.delete(username);
    this.saveState();
    this.channel.postMessage({ type: 'REMOVE_USER', data: username });
  }
  
  static getUserCount() {
    return this.users.size;
  }
  
  static getOtherUser(currentUser: string) {
    return Array.from(this.users).find(u => u !== currentUser);
  }
  
  private static setupChannelListener() {
    this.channel.onmessage = (event) => {
      const { type, data } = event.data;
      switch (type) {
        case 'ADD_USER':
          this.users.add(data);
          window.dispatchEvent(new CustomEvent('roomUpdate'));
          break;
        case 'REMOVE_USER':
          this.users.delete(data);
          window.dispatchEvent(new CustomEvent('roomUpdate'));
          break;
        case 'NEW_MESSAGE':
          this.messages.push(data);
          window.dispatchEvent(new CustomEvent('messageUpdate'));
          break;
      }
    };
  }
}

class ApiClient {
  private currentUsername?: string;
  private messageHandler?: () => void;
  private roomHandler?: () => void;

  // User Operations
  async joinRoom(username: string): Promise<JoinResponse> {
    this.currentUsername = username;
    MockStorage.addUser(username);
    const userCount = MockStorage.getUserCount();
    const otherUser = MockStorage.getOtherUser(username);
    
    return {
      status: userCount === 2 ? 'ready' : 'waiting',
      other_user: otherUser
    };
  }

  async leaveRoom(): Promise<void> {
    if (this.currentUsername) {
      MockStorage.removeUser(this.currentUsername);
      this.currentUsername = undefined;
    }
  }

  // Message Operations
  async sendBit(username: string, bit: 0 | 1): Promise<SendBitResponse> {
    const message: Message = {
      sender: username,
      bit: bit,
      timestamp: new Date().toLocaleTimeString()
    };
    
    MockStorage.addMessage(message);
    return { success: true };
  }

  // Start listening for updates
  startPolling(onMessages: (messages: Message[]) => void) {
    // Initial state
    onMessages(MockStorage.getMessages());
    
    // Message updates
    this.messageHandler = () => {
      onMessages(MockStorage.getMessages());
    };
    window.addEventListener('messageUpdate', this.messageHandler);

    // Room status updates
    this.roomHandler = () => {
      if (this.currentUsername) {
        const userCount = MockStorage.getUserCount();
        const otherUser = MockStorage.getOtherUser(this.currentUsername);
        window.dispatchEvent(new CustomEvent('roomStatusChange', {
          detail: {
            status: userCount === 2 ? 'ready' : 'waiting',
            other_user: otherUser
          }
        }));
      }
    };
    window.addEventListener('roomUpdate', this.roomHandler);
  }

  stopPolling() {
    if (this.messageHandler) {
      window.removeEventListener('messageUpdate', this.messageHandler);
      this.messageHandler = undefined;
    }
    if (this.roomHandler) {
      window.removeEventListener('roomUpdate', this.roomHandler);
      this.roomHandler = undefined;
    }
  }
}

export const api = new ApiClient(); 