import { useState, useEffect } from 'react';
import { Card } from '../ui/card';
import { Button } from '../ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../ui/tabs';
import { motion } from 'framer-motion';
import { cn } from '@/lib/utils';
import { QuantumCircuitDiagram } from './QuantumCircuitDiagram';
import { QuantumStateVisualizer } from './QuantumStateVisualizer';
import { QuantumTeleportationFlow } from './QuantumTeleportationFlow';

interface QuantumDashboardProps {
  className?: string;
}

const QuantumInfoCard = ({ title, description, icon, color }: { 
  title: string; 
  description: string; 
  icon: string; 
  color: string; 
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "p-6 rounded-lg border-2 transition-all hover:scale-105",
        color
      )}
    >
      <div className="flex items-center space-x-3 mb-3">
        <span className="text-2xl">{icon}</span>
        <h3 className="text-lg font-semibold text-white">{title}</h3>
      </div>
      <p className="text-sm text-zinc-300">{description}</p>
    </motion.div>
  );
};

const QuantumPrinciple = ({ principle, explanation, example }: {
  principle: string;
  explanation: string;
  example: string;
}) => {
  return (
    <Card className="p-4 bg-zinc-800 border-zinc-700">
      <h4 className="text-white font-semibold mb-2">{principle}</h4>
      <p className="text-sm text-zinc-300 mb-2">{explanation}</p>
      <div className="text-xs text-zinc-400 font-mono bg-zinc-900 p-2 rounded">
        {example}
      </div>
    </Card>
  );
};

export function QuantumDashboard({ className }: QuantumDashboardProps) {
  const [activeTab, setActiveTab] = useState('overview');

  const quantumPrinciples = [
    {
      principle: "Superposition",
      explanation: "A quantum system can exist in multiple states simultaneously until measured.",
      example: "|ψ⟩ = α|0⟩ + β|1⟩"
    },
    {
      principle: "Entanglement",
      explanation: "Two or more particles become correlated in such a way that the quantum state of each particle cannot be described independently.",
      example: "|Φ⁺⟩ = (|00⟩ + |11⟩)/√2"
    },
    {
      principle: "Measurement",
      explanation: "When a quantum system is measured, it collapses to one of its possible states.",
      example: "P(|0⟩) = |α|², P(|1⟩) = |β|²"
    }
  ];

  const quantumGates = [
    { name: "H", description: "Hadamard Gate", effect: "Creates superposition" },
    { name: "X", description: "Pauli-X Gate", effect: "Bit flip (NOT)" },
    { name: "CX", description: "CNOT Gate", effect: "Conditional NOT" },
    { name: "CZ", description: "Controlled-Z", effect: "Conditional phase" }
  ];

  const sampleCircuitData = {
    steps: [
      { step: 1, description: "Prepare qubit 0 in state |1⟩", qubits: [0] },
      { step: 2, description: "Create Bell pair between qubits 1 and 2", qubits: [1, 2] },
      { step: 3, description: "Bell measurement on qubits 0 and 1", qubits: [0, 1] },
      { step: 4, description: "Apply corrections on qubit 2", qubits: [2] },
      { step: 5, description: "Measure qubit 2 to recover state", qubits: [2] }
    ],
    gates: [
      { gate: "X", qubit: 0, step: 1 },
      { gate: "H", qubit: 1, step: 2 },
      { gate: "CX", control: 1, target: 2, step: 2 },
      { gate: "CX", control: 0, target: 1, step: 3 },
      { gate: "H", qubit: 0, step: 3 },
      { gate: "CX", control: 1, target: 2, step: 4 },
      { gate: "CZ", control: 0, target: 2, step: 4 }
    ]
  };

  return (
    <div className={cn("space-y-6", className)}>
      {/* Header */}
      <div className="text-center space-y-4">
        <motion.h1 
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-4xl font-bold text-white"
        >
          🌀 Quantum Teleportation Dashboard
        </motion.h1>
        <motion.p 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="text-zinc-400 max-w-2xl mx-auto"
        >
          Explore the fascinating world of quantum teleportation through interactive visualizations, 
          circuit diagrams, and real-time quantum state evolution.
        </motion.p>
      </div>

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <QuantumInfoCard
          title="Quantum Teleportation"
          description="Transfer quantum information from one qubit to another using entanglement and classical communication."
          icon="⚛️"
          color="bg-blue-500/10 border-blue-500/20"
        />
        <QuantumInfoCard
          title="Bell Pairs"
          description="Maximally entangled quantum states that serve as the quantum channel for teleportation."
          icon="🔗"
          color="bg-purple-500/10 border-purple-500/20"
        />
        <QuantumInfoCard
          title="Classical Communication"
          description="Two classical bits are sent to complete the teleportation protocol."
          icon="📡"
          color="bg-green-500/10 border-green-500/20"
        />
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4 bg-zinc-800">
          <TabsTrigger value="overview" className="text-zinc-300">Overview</TabsTrigger>
          <TabsTrigger value="circuit" className="text-zinc-300">Circuit</TabsTrigger>
          <TabsTrigger value="states" className="text-zinc-300">States</TabsTrigger>
          <TabsTrigger value="flow" className="text-zinc-300">Flow</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          {/* Quantum Principles */}
          <div>
            <h3 className="text-white font-semibold text-xl mb-4">Quantum Principles</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {quantumPrinciples.map((principle, index) => (
                <motion.div
                  key={principle.principle}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <QuantumPrinciple {...principle} />
                </motion.div>
              ))}
            </div>
          </div>

          {/* Quantum Gates */}
          <div>
            <h3 className="text-white font-semibold text-xl mb-4">Quantum Gates</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {quantumGates.map((gate, index) => (
                <motion.div
                  key={gate.name}
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  transition={{ delay: index * 0.1 }}
                >
                  <Card className="p-4 bg-zinc-800 border-zinc-700 text-center">
                    <div className="text-2xl font-bold text-blue-400 mb-2">{gate.name}</div>
                    <div className="text-sm text-zinc-300 mb-1">{gate.description}</div>
                    <div className="text-xs text-zinc-400">{gate.effect}</div>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Teleportation Process */}
          <div>
            <h3 className="text-white font-semibold text-xl mb-4">Teleportation Process</h3>
            <div className="bg-zinc-800 rounded-lg p-6">
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-bold">1</div>
                  <div>
                    <h4 className="text-white font-semibold">Prepare Input State</h4>
                    <p className="text-sm text-zinc-300">Initialize qubit 0 with the classical bit to be teleported</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="w-8 h-8 rounded-full bg-purple-500 flex items-center justify-center text-white font-bold">2</div>
                  <div>
                    <h4 className="text-white font-semibold">Create Bell Pair</h4>
                    <p className="text-sm text-zinc-300">Entangle qubits 1 and 2 using Hadamard and CNOT gates</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center text-white font-bold">3</div>
                  <div>
                    <h4 className="text-white font-semibold">Bell Measurement</h4>
                    <p className="text-sm text-zinc-300">Perform Bell measurement on qubits 0 and 1</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="w-8 h-8 rounded-full bg-yellow-500 flex items-center justify-center text-white font-bold">4</div>
                  <div>
                    <h4 className="text-white font-semibold">Classical Communication</h4>
                    <p className="text-sm text-zinc-300">Send classical measurement results to receiver</p>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="w-8 h-8 rounded-full bg-red-500 flex items-center justify-center text-white font-bold">5</div>
                  <div>
                    <h4 className="text-white font-semibold">Apply Corrections</h4>
                    <p className="text-sm text-zinc-300">Apply conditional operations on qubit 2 based on measurement</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </TabsContent>

        <TabsContent value="circuit" className="space-y-6">
          <QuantumCircuitDiagram 
            circuitData={sampleCircuitData}
            isAnimating={true}
          />
        </TabsContent>

        <TabsContent value="states" className="space-y-6">
          <QuantumStateVisualizer 
            teleportationData={sampleCircuitData}
          />
        </TabsContent>

        <TabsContent value="flow" className="space-y-6">
          <QuantumTeleportationFlow 
            teleportationData={sampleCircuitData}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
} 