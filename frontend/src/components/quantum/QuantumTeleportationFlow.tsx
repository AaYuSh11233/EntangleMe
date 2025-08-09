import { useState, useEffect } from 'react';
import { Card } from '../ui/card';
import { motion, AnimatePresence } from 'framer-motion';
import { cn } from '@/lib/utils';

interface QuantumTeleportationFlowProps {
  teleportationData: any;
  className?: string;
}

interface FlowStepProps {
  step: number;
  title: string;
  description: string;
  icon: string;
  isActive: boolean;
  isCompleted: boolean;
  delay?: number;
}

const FlowStep = ({ step, title, description, icon, isActive, isCompleted, delay = 0 }: FlowStepProps) => {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay }}
      className={cn(
        "flex items-start space-x-4 p-4 rounded-lg border-2 transition-all",
        isCompleted 
          ? "bg-green-500/10 border-green-500/40 text-green-300" 
          : isActive
          ? "bg-blue-500/10 border-blue-500/40 text-blue-300"
          : "bg-zinc-800 border-zinc-700 text-zinc-400"
      )}
    >
      <div className={cn(
        "w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold",
        isCompleted 
          ? "bg-green-500 text-white" 
          : isActive
          ? "bg-blue-500 text-white"
          : "bg-zinc-700 text-zinc-400"
      )}>
        {isCompleted ? '✓' : step}
      </div>
      <div className="flex-1">
        <div className="flex items-center space-x-2 mb-1">
          <span className="text-lg">{icon}</span>
          <h4 className="font-semibold">{title}</h4>
        </div>
        <p className="text-sm opacity-75">{description}</p>
      </div>
    </motion.div>
  );
};

const QuantumParticle = ({ isActive, isEntangled = false }: { isActive: boolean; isEntangled?: boolean }) => {
  return (
    <motion.div
      animate={{ 
        scale: isActive ? [1, 1.2, 1] : 1,
        rotate: isEntangled ? 360 : 0
      }}
      transition={{ 
        duration: 2,
        repeat: isEntangled ? Infinity : 0
      }}
      className={cn(
        "w-4 h-4 rounded-full",
        isEntangled 
          ? "bg-purple-500 shadow-lg shadow-purple-500/50" 
          : isActive 
          ? "bg-blue-500 shadow-lg shadow-blue-500/50"
          : "bg-zinc-600"
      )}
    />
  );
};

export function QuantumTeleportationFlow({ teleportationData, className }: QuantumTeleportationFlowProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  const flowSteps = [
    {
      step: 1,
      title: "Prepare Input State",
      description: "Initialize qubit 0 with the classical bit to be teleported",
      icon: "⚛️"
    },
    {
      step: 2,
      title: "Create Bell Pair",
      description: "Entangle qubits 1 and 2 using Hadamard and CNOT gates",
      icon: "🔗"
    },
    {
      step: 3,
      title: "Bell Measurement",
      description: "Perform Bell measurement on qubits 0 and 1",
      icon: "📊"
    },
    {
      step: 4,
      title: "Classical Communication",
      description: "Send classical measurement results to receiver",
      icon: "📡"
    },
    {
      step: 5,
      title: "Apply Corrections",
      description: "Apply conditional operations on qubit 2 based on measurement",
      icon: "🔧"
    },
    {
      step: 6,
      title: "State Recovery",
      description: "Measure qubit 2 to recover the teleported state",
      icon: "🎯"
    }
  ];

  useEffect(() => {
    if (isPlaying) {
      const interval = setInterval(() => {
        setCurrentStep((prev) => {
          if (prev >= flowSteps.length - 1) {
            setIsPlaying(false);
            return prev;
          }
          return prev + 1;
        });
      }, 2000);

      return () => clearInterval(interval);
    }
  }, [isPlaying, flowSteps.length]);

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
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-white font-semibold text-lg">Quantum Teleportation Flow</h3>
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

      {/* Flow Steps */}
      <div className="space-y-4">
        {flowSteps.map((step, index) => (
          <FlowStep
            key={step.step}
            step={step.step}
            title={step.title}
            description={step.description}
            icon={step.icon}
            isActive={index === currentStep}
            isCompleted={index < currentStep}
            delay={index * 0.1}
          />
        ))}
      </div>

      {/* Quantum Particles Visualization */}
      <div className="mt-8">
        <h4 className="text-white font-semibold mb-4">Quantum Particles</h4>
        <div className="flex justify-around items-center py-4">
          <div className="flex flex-col items-center space-y-2">
            <QuantumParticle isActive={currentStep >= 0} />
            <span className="text-xs text-zinc-400">Qubit 0</span>
          </div>
          <motion.div
            animate={{ 
              scale: currentStep >= 1 ? [1, 1.1, 1] : 1,
              opacity: currentStep >= 1 ? 1 : 0.3
            }}
            transition={{ duration: 0.5 }}
            className="flex items-center space-x-2"
          >
            <QuantumParticle isActive={currentStep >= 1} isEntangled={currentStep >= 1} />
            <span className="text-zinc-400">⟷</span>
            <QuantumParticle isActive={currentStep >= 1} isEntangled={currentStep >= 1} />
          </motion.div>
          <div className="flex flex-col items-center space-y-2">
            <span className="text-xs text-zinc-400">Qubits 1 & 2</span>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mt-6">
        <div className="flex justify-between text-sm text-zinc-400 mb-2">
          <span>Progress</span>
          <span>{Math.round(((currentStep + 1) / flowSteps.length) * 100)}%</span>
        </div>
        <div className="w-full bg-zinc-700 rounded-full h-2">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${((currentStep + 1) / flowSteps.length) * 100}%` }}
            transition={{ duration: 0.5 }}
            className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full"
          />
        </div>
      </div>

      {/* Current Step Info */}
      {flowSteps[currentStep] && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-4 p-3 bg-zinc-800 rounded"
        >
          <div className="text-sm text-zinc-300">
            <strong>Current Step {currentStep + 1}:</strong> {flowSteps[currentStep].title}
          </div>
        </motion.div>
      )}
    </Card>
  );
} 