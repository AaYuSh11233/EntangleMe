import { Card } from '../ui/card';
import { TeleportationResult } from '@/types/quantum';

interface QuantumVisualizerProps {
  result?: TeleportationResult;
}

export function QuantumVisualizer({ result }: QuantumVisualizerProps) {
  if (!result) {
    return null;
  }

  return (
    <Card className="p-4">
      <div className="space-y-4">
        <h3 className="text-lg font-medium">Teleportation Result</h3>
        <div className="grid gap-4">
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Classical Bits</h4>
            <div className="font-mono text-lg">
              {result.classicalBits}
            </div>
          </div>
          <div className="space-y-2">
            <h4 className="text-sm font-medium">Receiver's State</h4>
            <div className="font-mono text-lg">
              |{result.receiverState}⟩
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
} 