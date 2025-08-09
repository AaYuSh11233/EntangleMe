import { JoinResponse, Message, SendBitResponse } from '../types/chat';
import { TeleportationResult } from '../types/quantum';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

class ApiClient {
  private currentUsername?: string;
  private currentUserId?: string;
  private roomId?: string;
  private messageHandler?: () => void;
  private roomHandler?: () => void;

  async getUserByUsername(username: string) {
    const res = await fetch(`${API_BASE_URL}/chat/users/${username}`);
    if (!res.ok) throw new Error("Failed to fetch user");
    return await res.json();
  }

  // User Operations
  async joinRoom(username: string): Promise<JoinResponse> {
    try {
      console.log('Joining room with username:', username);

      // Try to create user first
      let userData;
      let userResponse = await fetch(`${API_BASE_URL}/chat/users`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username,
          email: `${username}@entangleme.local`
        })
      });

      if (!userResponse.ok) {
        const errorText = await userResponse.text();
        // If username exists, fetch the user instead of failing
        if (
          userResponse.status === 400 &&
          errorText.includes("Username already exists")
        ) {
          userData = await this.getUserByUsername(username);
          console.log('Fetched existing user:', userData);
        } else {
          console.error('User creation failed:', userResponse.status, errorText);
          throw new Error(`Failed to create user: ${userResponse.status} ${errorText}`);
        }
      } else {
        userData = await userResponse.json();
        console.log('User created:', userData);
      }

      this.currentUserId = userData.id;
      this.currentUsername = username;

      // Join the default room
      const roomResponse = await fetch(`${API_BASE_URL}/chat/rooms`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: 'Entangle Room',
          participant_ids: [this.currentUserId]
        })
      });

      if (!roomResponse.ok) {
        const errorText = await roomResponse.text();
        console.error('Room creation failed:', roomResponse.status, errorText);
        throw new Error(`Failed to join room: ${roomResponse.status} ${errorText}`);
      }

      const roomData = await roomResponse.json();
      console.log('Room created:', roomData);
      this.roomId = roomData.id;

      // Get room participants
      const participantsResponse = await fetch(`${API_BASE_URL}/chat/rooms/${this.roomId}/participants`);
      if (participantsResponse.ok) {
        const participants = await participantsResponse.json();
        console.log('Room participants:', participants);
        const otherUser = participants.find((p: any) => p.id !== this.currentUserId);

        return {
          status: participants.length === 2 ? 'ready' : 'waiting',
          other_user: otherUser?.username
        };
      }

      return {
        status: 'waiting',
        other_user: undefined
      };
    } catch (error) {
      console.error('Error joining room:', error);
      throw error;
    }
  }

  async leaveRoom(): Promise<void> {
    if (this.currentUserId && this.roomId) {
      try {
        await fetch(`${API_BASE_URL}/chat/rooms/${this.roomId}/participants/${this.currentUserId}`, {
          method: 'DELETE'
        });
      } catch (error) {
        console.error('Error leaving room:', error);
      }
    }
    this.currentUserId = undefined;
    this.currentUsername = undefined;
    this.roomId = undefined;
  }

  // Message Operations
  async sendBit(username: string, bit: 0 | 1): Promise<SendBitResponse> {
    if (!this.currentUserId || !this.roomId) {
      throw new Error('Not in a room');
    }

    try {
      // Get other user in room
      const participantsResponse = await fetch(`${API_BASE_URL}/chat/rooms/${this.roomId}/participants`);
      const participants = await participantsResponse.json();
      const receiver = participants.find((p: any) => p.id !== this.currentUserId);

      if (!receiver) {
        throw new Error('No receiver found');
      }

      // Perform quantum teleportation
      const teleportResponse = await fetch(`${API_BASE_URL}/quantum/teleport`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sender_id: this.currentUserId,
          receiver_id: receiver.id,
          classical_bit: bit,
          room_id: this.roomId,
          message_content: `Teleported bit: ${bit}`
        })
      });

      if (!teleportResponse.ok) {
        const errorText = await teleportResponse.text();
        throw new Error(`Quantum teleportation failed: ${teleportResponse.status} ${errorText}`);
      }

      const teleportResult = await teleportResponse.json();
      
      return { 
        success: teleportResult.success,
        teleportation_result: teleportResult
      };
    } catch (error) {
      console.error('Error sending bit:', error);
      throw error;
    }
  }

  async getMessages(): Promise<Message[]> {
    if (!this.roomId) {
      return [];
    }

    try {
      const response = await fetch(`${API_BASE_URL}/chat/rooms/${this.roomId}/messages`);
      if (!response.ok) {
        throw new Error('Failed to fetch messages');
      }

      const messages = await response.json();
      return messages.map((msg: any) => ({
        sender: msg.sender_username,
        bit: msg.quantum_state ? parseInt(msg.quantum_state) : 0,
        timestamp: new Date(msg.created_at).toLocaleTimeString(),
        teleportation_result: msg.teleportation_result
      }));
    } catch (error) {
      console.error('Error fetching messages:', error);
      return [];
    }
  }

  // Quantum Operations
  async simulateTeleportation(bit: 0 | 1): Promise<TeleportationResult> {
    try {
      const response = await fetch(`${API_BASE_URL}/quantum/simulate?bit=${bit}`, {
        method: 'POST'
      });

      if (!response.ok) {
        throw new Error('Simulation failed');
      }

      const result = await response.json();
    return {
        success: result.result.success,
        receiverState: result.result.received_bit,
        classicalBits: result.result.classical_bits
      };
    } catch (error) {
      console.error('Error simulating teleportation:', error);
      throw error;
    }
  }

  async getCircuitVisualization(bit: 0 | 1): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/quantum/circuit/${bit}`);
      if (!response.ok) {
        throw new Error('Failed to get circuit visualization');
      }
      return await response.json();
    } catch (error) {
      console.error('Error getting circuit visualization:', error);
      throw error;
    }
  }

  // Start polling for updates
  startPolling(onMessages: (messages: Message[]) => void, onRoomUpdate: (status: string) => void) {
    const pollMessages = async () => {
      try {
        const messages = await this.getMessages();
        onMessages(messages);
      } catch (error) {
        console.error('Error polling messages:', error);
      }
    };

    const pollRoomStatus = async () => {
      if (this.roomId) {
        try {
          const participantsResponse = await fetch(`${API_BASE_URL}/chat/rooms/${this.roomId}/participants`);
          if (participantsResponse.ok) {
            const participants = await participantsResponse.json();
            const status = participants.length === 2 ? 'ready' : 'waiting';
            onRoomUpdate(status);
          }
        } catch (error) {
          console.error('Error polling room status:', error);
        }
      }
    };

    // Initial poll
    pollMessages();
    pollRoomStatus();

    // Set up polling interval
    this.messageHandler = setInterval(pollMessages, 2000);
    this.roomHandler = setInterval(pollRoomStatus, 3000);
  }

  stopPolling() {
    if (this.messageHandler) {
      clearInterval(this.messageHandler);
      this.messageHandler = undefined;
    }
    if (this.roomHandler) {
      clearInterval(this.roomHandler);
      this.roomHandler = undefined;
    }
  }
}

export const api = new ApiClient();