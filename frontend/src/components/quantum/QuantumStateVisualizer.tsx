import { useState, useEffect } from 'react';
import { Card } from '../ui/card';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

interface QuantumStateVisualizerProps {
  teleportationData: any;
  className?: string;
}

interface StateVectorProps {
  state: string;
  probability: number;
  isActive?: boolean;
  delay?: number;
}

const StateVector = ({ state, probability, isActive = false, delay = 0 }: StateVectorProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.8 }}
      animate={{ opacity: isActive ? 1 : 0.6, scale: isActive ? 1 : 0.9 }}
      transition={{ delay, duration: 0.3 }}
      className={cn(
        "flex items-center justify-between p-3 rounded-lg border-2 transition-all",
        isActive 
          ? "bg-blue-500/20 border-blue-500/40 text-blue-300" 
          : "bg-zinc-800 border-zinc-700 text-zinc-400"
      )}
    >
      <div className="font-mono text-sm">{state}</div>
      <div className="text-xs opacity-75">{probability.toFixed(2)}</div>
    </motion.div>
  );
};

const BlochSphere = ({ qubit, state }: { qubit: number; state: string }) => {
  const getStateColor = (state: string) => {
    switch (state) {
      case '|0⟩': return 'bg-blue-500';
      case '|1⟩': return 'bg-red-500';
      case '|+⟩': return 'bg-green-500';
      case '|-⟩': return 'bg-purple-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <div className="flex flex-col items-center space-y-2">
      <div className="relative">
        <div className="w-16 h-16 rounded-full border-2 border-zinc-600 flex items-center justify-center bg-zinc-800">
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ duration: 0.5 }}
            className={cn(
              "w-8 h-8 rounded-full",
              getStateColor(state)
            )}
          />
        </div>
        <div className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-zinc-700 flex items-center justify-center text-xs font-bold">
          {qubit}
        </div>
      </div>
      <div className="text-xs text-zinc-400 font-mono">{state}</div>
    </div>
  );
};

export function QuantumStateVisualizer({ teleportationData, className }: QuantumStateVisualizerProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const steps = teleportationData?.steps || [];
  const states = [
    { state: '|0⟩', probability: 0.5 },
    { state: '|1⟩', probability: 0.5 },
    { state: '|+⟩', probability: 0.25 },
    { state: '|-⟩', probability: 0.25 }
  ];

  useEffect(() => {
    if (isPlaying) {
      const interval = setInterval(() => {
        setCurrentStep((prev) => {
          if (prev >= steps.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 1500);

      return () => clearInterval(interval);
    }
  }, [isPlaying, steps.length]);

  const handlePlay = () => {
    setCurrentStep(0);
    setIsPlaying(true);
  };

  const handleReset = () => {
    setCurrentStep(0);
    setIsPlaying(false);
  };

  return (
    <Card className={cn("p-6 bg-zinc-900 border-zinc-800", className)}>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-white font-semibold text-lg">Quantum State Evolution</h3>
        <div className="flex items-center space-x-2">
          <button
            onClick={handleReset}
            className="px-3 py-1 text-xs bg-zinc-700 text-zinc-300 rounded hover:bg-zinc-600"
          >
            Reset
          </button>
          <button
            onClick={isPlaying ? () => setIsPlaying(false) : handlePlay}
            className="px-3 py-1 text-xs bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            {isPlaying ? 'Pause' : 'Play'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* State Vectors */}
        <div>
          <h4 className="text-white font-semibold mb-3">State Vectors</h4>
          <div className="space-y-2">
            {states.map((state, index) => (
              <StateVector
                key={state.state}
                state={state.state}
                probability={state.probability}
                isActive={currentStep >= index}
                delay={index * 0.1}
              />
            ))}
          </div>
        </div>

        {/* Bloch Spheres */}
        <div>
          <h4 className="text-white font-semibold mb-3">Qubit States (Bloch Sphere)</h4>
          <div className="flex justify-around">
            <BlochSphere qubit={0} state={currentStep === 0 ? '|0⟩' : '|1⟩'} />
            <BlochSphere qubit={1} state={currentStep >= 1 ? '|+⟩' : '|0⟩'} />
            <BlochSphere qubit={2} state={currentStep >= 2 ? '|+⟩' : '|0⟩'} />
          </div>
        </div>
      </div>

      {/* Step Information */}
      <div className="mt-6 p-3 bg-zinc-800 rounded">
        <div className="text-sm text-zinc-400 mb-2">
          Step: {currentStep + 1} / {steps.length}
        </div>
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

      {/* Entanglement Visualization */}
      <div className="mt-4">
        <h4 className="text-white font-semibold mb-3">Entanglement Status</h4>
        <div className="flex items-center space-x-4">
          <motion.div
            animate={{ scale: currentStep >= 1 ? [1, 1.2, 1] : 1 }}
            transition={{ duration: 0.5 }}
            className={cn(
              "w-4 h-4 rounded-full",
              currentStep >= 1 ? "bg-green-500" : "bg-zinc-600"
            )}
          />
          <span className="text-sm text-zinc-300">
            {currentStep >= 1 ? "Entangled" : "Not Entangled"}
          </span>
        </div>
      </div>
    </Card>
  );
} 