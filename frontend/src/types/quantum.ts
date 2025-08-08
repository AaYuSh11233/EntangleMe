export interface TeleportationResult {
  success: boolean;
  receiverState: 0 | 1;
  classicalBits?: string; // Optional: For showing the quantum circuit details
} 