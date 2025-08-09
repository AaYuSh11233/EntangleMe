export interface TeleportationResult {
  success: boolean;
  sent_bit: number;
  received_bit: number;
  classical_bits: string;
  receiver_state: string;
  teleportation_data: {
    circuit: any;
    measurements: any[];
    gates: any[];
    steps: any[];
  };
  success_probability: number;
  measurement_results: {
    classical_bits: string;
    received_bit: number;
    success: boolean;
  };
}

export interface CircuitVisualization {
  bit: number;
  circuit_data: {
    circuit_text: string;
    circuit_data: any;
    num_qubits: number;
    num_classical_bits: number;
    depth: number;
    gate_count: any;
  };
  description: string;
} 