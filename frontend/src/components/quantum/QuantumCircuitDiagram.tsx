import { useState, useEffect } from 'react';
import { Card } from '../ui/card';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

interface QuantumCircuitDiagramProps {
  circuitData: any;
  isAnimating?: boolean;
  className?: string;
}

interface GateProps {
  gate: string;
  qubit: number;
  step: number;
  isActive?: boolean;
  delay?: number;
}

const Gate = ({ gate, qubit, step, isActive = false, delay = 0 }: GateProps) => {
  const gateColors = {
    'H': 'bg-yellow-500',
    'X': 'bg-red-500',
    'CX': 'bg-blue-500',
    'CZ': 'bg-purple-500',
    'M': 'bg-green-500'
  };

  const gateColor = gateColors[gate as keyof typeof gateColors] || 'bg-gray-500';

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: isActive ? 1 : 0.6, scale: isActive ? 1.1 : 1 }}
      transition={{ delay, duration: 0.3 }}
      className={cn(
        "w-8 h-8 rounded flex items-center justify-center text-white text-xs font-bold border-2",
        gateColor,
        isActive ? "border-white shadow-lg" : "border-transparent"
      )}
    >
      {gate}
    </motion.div>
  );
};

const QubitLine = ({ qubit, gates, currentStep }: { qubit: number; gates: any[]; currentStep: number }) => {
  const qubitGates = gates.filter((gate: any) => gate.qubit === qubit || gate.control === qubit || gate.target === qubit);

  return (
    <div className="flex items-center space-x-4 py-2">
      <div className="w-12 text-right text-sm text-zinc-400 font-mono">
        q_{qubit}
      </div>
      <div className="flex-1 flex items-center space-x-4 relative">
        {qubitGates.map((gate: any, index: number) => (
          <Gate
            key={`${gate.gate}-${gate.qubit}-${index}`}
            gate={gate.gate}
            qubit={qubit}
            step={gate.step}
            isActive={gate.step <= currentStep}
            delay={index * 0.1}
          />
        ))}
        <div className="flex-1 h-0.5 bg-zinc-600"></div>
      </div>
    </div>
  );
};

export function QuantumCircuitDiagram({ circuitData, isAnimating = true, className }: QuantumCircuitDiagramProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const steps = circuitData?.steps || [];
  const gates = circuitData?.gates || [];

  useEffect(() => {
    if (isAnimating && isPlaying) {
      const interval = setInterval(() => {
        setCurrentStep((prev) => {
          if (prev >= steps.length) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [isAnimating, isPlaying, steps.length]);

  const handlePlay = () => {
    setCurrentStep(0);
    setIsPlaying(true);
  };

  const handleReset = () => {
    setCurrentStep(0);
    setIsPlaying(false);
  };

  const handleStepForward = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleStepBackward = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  return (
    <Card className={cn("p-6 bg-zinc-900 border-zinc-800", className)}>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-white font-semibold text-lg">Quantum Circuit Diagram</h3>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleReset}
            className="px-3 py-1 text-xs bg-zinc-700 text-zinc-300 rounded hover:bg-zinc-600"
          >
            Reset
          </button>
          <button
            onClick={handleStepBackward}
            disabled={currentStep === 0}
            className="px-3 py-1 text-xs bg-zinc-700 text-zinc-300 rounded hover:bg-zinc-600 disabled:opacity-50"
          >
            ←
          </button>
          <button
            onClick={isPlaying ? () => setIsPlaying(false) : handlePlay}
            className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            {isPlaying ? 'Pause' : 'Play'}
          </button>
          <button
            onClick={handleStepForward}
            disabled={currentStep >= steps.length}
            className="px-3 py-1 text-xs bg-zinc-700 text-zinc-300 rounded hover:bg-zinc-600 disabled:opacity-50"
          >
            →
          </button>
        </div>
      </div>

      <div className="space-y-2">
        {[0, 1, 2].map((qubit) => (
          <QubitLine
            key={qubit}
            qubit={qubit}
            gates={gates}
            currentStep={currentStep}
          />
        ))}
      </div>

      <div className="mt-4 p-3 bg-zinc-800 rounded">
        <div className="text-sm text-zinc-400 mb-2">Current Step: {currentStep + 1} / {steps.length}</div>
        {steps[currentStep] && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-sm text-zinc-300"
          >
            <strong>Step {steps[currentStep].step}:</strong> {steps[currentStep].description}
          </motion.div>
        )}
      </div>
    </Card>
  );
} 