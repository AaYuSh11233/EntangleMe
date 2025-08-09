import { useState } from 'react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../ui/dialog';
import { TeleportationResult } from '@/types/quantum';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';

interface QuantumVisualizerProps {
  teleportationResult?: TeleportationResult;
  bit: 0 | 1;
}

export function QuantumVisualizer({ teleportationResult, bit }: QuantumVisualizerProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!teleportationResult) return null;

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button 
          variant="outline" 
          size="sm"
          className="text-xs bg-blue-500/10 border-blue-500/20 text-blue-400 hover:bg-blue-500/20"
        >
          📊 View Quantum Details
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto bg-zinc-900 border-zinc-800">
        <DialogHeader>
          <DialogTitle className="text-white">
            Quantum Teleportation Circuit - Bit {bit}
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-6">
          {/* Success Status */}
          <div className={cn(
            "p-4 rounded-lg border",
            teleportationResult.success 
              ? "bg-green-500/10 border-green-500/20 text-green-400"
              : "bg-red-500/10 border-red-500/20 text-red-400"
          )}>
            <div className="font-semibold mb-2">
              {teleportationResult.success ? "✅ Teleportation Successful" : "❌ Teleportation Failed"}
            </div>
            <div className="text-sm space-y-1">
              <div>Sent: {teleportationResult.sent_bit}</div>
              <div>Received: {teleportationResult.received_bit}</div>
              <div>Success Probability: {(teleportationResult.success_probability * 100).toFixed(1)}%</div>
            </div>
          </div>

          {/* Classical Bits */}
          <Card className="p-4 bg-zinc-800 border-zinc-700">
            <h3 className="text-white font-semibold mb-2">Classical Measurement Results</h3>
            <div className="font-mono text-sm text-blue-400 bg-zinc-900 p-2 rounded">
              {teleportationResult.classical_bits}
            </div>
            <div className="text-xs text-zinc-400 mt-1">
              Binary string representing measurement outcomes
            </div>
          </Card>

          {/* Circuit Steps */}
          <Card className="p-4 bg-zinc-800 border-zinc-700">
            <h3 className="text-white font-semibold mb-2">Circuit Steps</h3>
            <div className="space-y-2">
              {teleportationResult.teleportation_data.steps.map((step: any, index: number) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="flex items-center gap-3 p-2 bg-zinc-900 rounded"
                >
                  <div className="w-6 h-6 rounded-full bg-blue-500/20 flex items-center justify-center text-xs text-blue-400">
                    {step.step}
                  </div>
                  <div className="text-sm text-zinc-300">
                    {step.description}
                  </div>
                  <div className="text-xs text-zinc-500">
                    Qubits: {step.qubits.join(', ')}
                  </div>
                </motion.div>
              ))}
            </div>
          </Card>

          {/* Quantum Gates */}
          <Card className="p-4 bg-zinc-800 border-zinc-700">
            <h3 className="text-white font-semibold mb-2">Quantum Gates Applied</h3>
            <div className="grid grid-cols-2 gap-2">
              {teleportationResult.teleportation_data.gates.map((gate: any, index: number) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.05 }}
                  className="p-2 bg-zinc-900 rounded text-xs"
                >
                  <div className="font-semibold text-purple-400">{gate.gate}</div>
                  <div className="text-zinc-400">
                    {gate.qubit !== undefined && `Qubit: ${gate.qubit}`}
                    {gate.control !== undefined && `Control: ${gate.control}`}
                    {gate.target !== undefined && `Target: ${gate.target}`}
                  </div>
                  <div className="text-zinc-500">Step: {gate.step}</div>
                </motion.div>
              ))}
            </div>
          </Card>

          {/* Circuit Diagram */}
          <Card className="p-4 bg-zinc-800 border-zinc-700">
            <h3 className="text-white font-semibold mb-2">Circuit Diagram</h3>
            <div className="font-mono text-xs text-green-400 bg-black p-4 rounded overflow-x-auto">
              <pre>{teleportationResult.teleportation_data.circuit.circuit_text}</pre>
            </div>
          </Card>
        </div>
      </DialogContent>
    </Dialog>
  );
}
