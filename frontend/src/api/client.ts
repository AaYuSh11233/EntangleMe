import { JoinResponse, Message, SendBitResponse } from '../types/chat';

// Simulated storage using localStorage
class MockStorage {
  private static USERS_KEY = 'entangleme_users';
  private static MESSAGES_KEY = 'entangleme_messages';
  
  private static getStoredUsers(): string[] {
    const stored = localStorage.getItem(this.USERS_KEY);
    return stored ? JSON.parse(stored) : [];
  }
  
  private static getStoredMessages(): Message[] {
    const stored = localStorage.getItem(this.MESSAGES_KEY);
    return stored ? JSON.parse(stored) : [];
  }
  
  static addMessage(message: Message) {
    const messages = this.getStoredMessages();
    messages.push(message);
    localStorage.setItem(this.MESSAGES_KEY, JSON.stringify(messages));
  }
  
  static getMessages(): Message[] {
    return this.getStoredMessages();
  }
  
  static addUser(username: string) {
    const users = this.getStoredUsers();
    if (!users.includes(username)) {
      users.push(username);
      localStorage.setItem(this.USERS_KEY, JSON.stringify(users));
    }
  }
  
  static removeUser(username: string) {
    const users = this.getStoredUsers().filter(u => u !== username);
    localStorage.setItem(this.USERS_KEY, JSON.stringify(users));
  }
  
  static getUserCount() {
    return this.getStoredUsers().length;
  }
  
  static getFirstUser() {
    return this.getStoredUsers()[0];
  }
  
  static getOtherUser(currentUser: string) {
    return this.getStoredUsers().find(u => u !== currentUser);
  }
  
  static clearAll() {
    localStorage.removeItem(this.MESSAGES_KEY);
    localStorage.removeItem(this.USERS_KEY);
  }
  
  // Added for real-time updates
  static onStorageChange(callback: () => void) {
    window.addEventListener('storage', callback);
    return () => window.removeEventListener('storage', callback);
  }
}

class ApiClient {
  private storageListener?: () => void;
  private currentUsername?: string;

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

  async getMessages(): Promise<Message[]> {
    return MockStorage.getMessages();
  }

  // Real-time updates using storage events
  startPolling(onMessages: (messages: Message[]) => void) {
    // Initial messages
    onMessages(MockStorage.getMessages());
    
    // Set up storage event listener for real-time updates
    this.storageListener = () => {
      onMessages(MockStorage.getMessages());
      
      // Check if user count has changed
      if (this.currentUsername) {
        const userCount = MockStorage.getUserCount();
        const otherUser = MockStorage.getOtherUser(this.currentUsername);
        
        // Dispatch a custom event when room status changes
        window.dispatchEvent(new CustomEvent('roomStatusChange', {
          detail: {
            status: userCount === 2 ? 'ready' : 'waiting',
            other_user: otherUser
          }
        }));
      }
    };
    
    // Add the storage event listener
    window.addEventListener('storage', this.storageListener);
  }

  stopPolling() {
    if (this.storageListener) {
      window.removeEventListener('storage', this.storageListener);
      this.storageListener = undefined;
    }
  }
}

export const api = new ApiClient(); 