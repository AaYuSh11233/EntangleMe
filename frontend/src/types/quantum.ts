export type QubitState = "0" | "1";

export interface TeleportationResult {
  classicalBits: string;
  receiverState: string;
}

export interface QuantumMessage {
  state: QubitState;
  result?: TeleportationResult;
  timestamp: number;
  senderId: string;
  receiverId: string;
} 