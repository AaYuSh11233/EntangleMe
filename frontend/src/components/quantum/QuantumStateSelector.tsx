import { useState } from 'react';
import { Button } from '../ui/button';
import { Card } from '../ui/card';
import { QubitState } from '@/types/quantum';
import { toast } from 'sonner';
import { api } from '@/api/client';

interface QuantumStateSelectorProps {
  onStateSelected?: (state: QubitState, result: { classicalBits: string; receiverState: string }) => void;
}

export function QuantumStateSelector({ onStateSelected }: QuantumStateSelectorProps) {
  const [isLoading, setIsLoading] = useState(false);

  const handleStateSelect = async (state: QubitState) => {
    setIsLoading(true);
    try {
      const result = await api.teleport(state);
      toast.success('State teleported successfully!');
      onStateSelected?.(state, result);
    } catch (error) {
      toast.error('Failed to teleport state');
      console.error('Teleportation error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="p-4">
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Select Quantum State</h3>
        <p className="text-sm text-muted-foreground">
          Choose a qubit state to teleport
        </p>
        <div className="flex gap-4">
          <Button
            variant="outline"
            onClick={() => handleStateSelect("0")}
            disabled={isLoading}
          >
            |0⟩
          </Button>
          <Button
            variant="outline"
            onClick={() => handleStateSelect("1")}
            disabled={isLoading}
          >
            |1⟩
          </Button>
        </div>
      </div>
    </Card>
  );
} 