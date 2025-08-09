# 🌀 Quantum Circuit Diagram - EntangleMe

## ⚛️ **Quantum Teleportation Circuit Visualization**

### **Complete Circuit Diagram**

```
     ┌───┐     ┌───┐     ┌───┐     ┌───┐     ┌───┐
q_0: ┤ X ├─────┤ X ├─────┤ H ├─────┤ X ├─────┤ Z ├─────┤M├
     └───┘     └─┬─┘     └───┘     └─┬─┘     └─┬─┘     └╥┘
q_1: ────────────┼─────────┼─────────┼─────────┼─────────╫─
                 │         │         │         │         ║
q_2: ────────────┼─────────┼─────────┼─────────┼─────────╫─
                 │         │         │         │         ║
     ┌───┐     ┌─┴─┐     ┌─┴─┐     ┌─┴─┐     ┌─┴─┐     ║
q_1: ┤ H ├─────┤ X ├─────┤ X ├─────┤ X ├─────┤ X ├─────╫─
     └───┘     └───┘     └───┘     └───┘     └───┘     ║
                                                        ║
q_2: ────────────┼─────────┼─────────┼─────────┼─────────╫─
                 │         │         │         │         ║
     ┌───┐     ┌─┴─┐     ┌─┴─┐     ┌─┴─┐     ┌─┴─┐     ║
q_2: ┤ H ├─────┤ X ├─────┤ X ├─────┤ X ├─────┤ X ├─────╫─
     └───┘     └───┘     └───┘     └───┘     └───┘     ║
                                                        ║
c: 3/═══════════════════════════════════════════════════╩═
                                                        0
```

### **Step-by-Step Circuit Breakdown**

#### **Step 1: Input State Preparation**
```
q_0: ┤ X ├  (only if input = 1)
     └───┘
q_1: ─────
q_2: ─────
```
- **Purpose**: Prepare qubit 0 in the desired state (|0⟩ or |1⟩)
- **Action**: Apply X gate if input is 1, otherwise leave as |0⟩
- **Result**: |ψ⟩₀ = α|0⟩₀ + β|1⟩₀

#### **Step 2: Bell Pair Creation**
```
q_0: ─────
q_1: ┤ H ├──┐
     └───┘  │
q_2: ───────┼──
            │
q_1: ───────┼──
            │
q_2: ───────┼──
            │
     ┌──────┴──┐
q_1: ┤         ├
     └─────────┘
q_2: ┤    X    ├
     └─────────┘
```
- **Purpose**: Create entanglement between qubits 1 and 2
- **Action**: H gate on qubit 1, then CX(1,2)
- **Result**: |Φ⁺⟩₁₂ = (|00⟩₁₂ + |11⟩₁₂)/√2

#### **Step 3: Bell Measurement**
```
q_0: ─────┐
          │
q_1: ─────┼──┐
          │  │
q_0: ┤ X ├──┼──┐
     └───┘  │  │
q_1: ───────┼──┼──┐
            │  │  │
q_0: ┤ H ├──┼──┼──┐
     └───┘  │  │  │
q_1: ───────┼──┼──┼──┐
            │  │  │  │
q_0: ───────┼──┼──┼──┼──┐
            │  │  │  │  │
q_1: ───────┼──┼──┼──┼──┼──┐
            │  │  │  │  │  │
     ┌──────┴──┴──┴──┴──┴──┴──┐
q_0: ┤                        ├
     └────────────────────────┘
q_1: ┤           M            ├
     └────────────────────────┘
```
- **Purpose**: Perform Bell measurement on qubits 0 and 1
- **Action**: CX(0,1), then H(0), then measure both
- **Result**: 2 classical bits (00, 01, 10, or 11)

#### **Step 4: Conditional Operations**
```
q_0: ─────┐
          │
q_1: ─────┼──┐
          │  │
q_2: ─────┼──┼──┐
          │  │  │
q_1: ─────┼──┼──┼──┐
          │  │  │  │
q_2: ─────┼──┼──┼──┼──┐
          │  │  │  │  │
     ┌────┴──┴──┴──┴──┴──┐
q_1: ┤                   ├
     └───────────────────┘
q_2: ┤         X         ├
     └───────────────────┘
q_0: ─────┐
          │
q_2: ─────┼──┐
          │  │
     ┌────┴──┴──┐
q_0: ┤          ├
     └──────────┘
q_2: ┤     Z    ├
     └──────────┘
```
- **Purpose**: Apply corrections to qubit 2 based on measurement results
- **Action**: CX(1,2) and CZ(0,2)
- **Result**: Recovered teleported state on qubit 2

#### **Step 5: Final Measurement**
```
q_2: ─────┐
          │
     ┌────┴──┐
q_2: ┤       ├
     └───────┘
q_2: ┤   M   ├
     └───────┘
```
- **Purpose**: Measure qubit 2 to recover the teleported state
- **Action**: Measure qubit 2
- **Result**: Classical bit (0 or 1) - the teleported state

### **Quantum State Evolution**

```
Initial State: |ψ⟩₀ ⊗ |0⟩₁ ⊗ |0⟩₂
                │
                ▼
Step 1: |ψ⟩₀ ⊗ |0⟩₁ ⊗ |0⟩₂
        │
        ▼
Step 2: |ψ⟩₀ ⊗ |Φ⁺⟩₁₂
        │
        ▼
Step 3: Bell measurement → Classical bits
        │
        ▼
Step 4: Conditional operations
        │
        ▼
Step 5: |ψ⟩₂ (teleported state)
```

### **Measurement Outcomes**

```
Possible Measurement Results:
┌─────────┬─────────┬─────────┬─────────┬─────────┐
│ Outcome │ Bit 0   │ Bit 1   │ Bit 2   │ Success │
├─────────┼─────────┼─────────┼─────────┼─────────┤
│   000   │    0    │    0    │    0    │   ✅    │
│   001   │    0    │    0    │    1    │   ✅    │
│   010   │    0    │    1    │    0    │   ✅    │
│   011   │    0    │    1    │    1    │   ✅    │
│   100   │    1    │    0    │    0    │   ✅    │
│   101   │    1    │    0    │    1    │   ✅    │
│   110   │    1    │    1    │    0    │   ✅    │
│   111   │    1    │    1    │    1    │   ✅    │
└─────────┴─────────┴─────────┴─────────┴─────────┘
```

### **Quantum Gates Used**

```
┌─────────────────────────────────────────────────────────────────┐
│                        QUANTUM GATES                            │
│                                                                 │
│  ┌───┐     ┌───┐     ┌───┐     ┌───┐                          │
│  │ H │     │ X │     │CX │     │ Z │                          │
│  └───┘     └───┘     └───┘     └───┘                          │
│   │         │         │         │                              │
│   │         │         │         │                              │
│ Hadamard   Pauli-X   CNOT     Pauli-Z                         │
│   │         │         │         │                              │
│   │         │         │         │                              │
│ |0⟩→|+⟩   |0⟩→|1⟩   |00⟩→|00⟩  |0⟩→|0⟩                        │
│ |1⟩→|-⟩   |1⟩→|0⟩   |01⟩→|01⟩  |1⟩→-|1⟩                       │
│           |10⟩→|11⟩                                           │
│           |11⟩→|10⟩                                           │
└─────────────────────────────────────────────────────────────────┘
```

### **Entanglement Visualization**

```
Bell Pair Creation:
┌─────────────────────────────────────────────────────────────────┐
│                      BELL PAIR CREATION                         │
│                                                                 │
│  Initial: |0⟩₁ ⊗ |0⟩₂                                         │
│     │                                                          │
│     ▼                                                          │
│  H gate: (|0⟩₁ + |1⟩₁)/√2 ⊗ |0⟩₂                              │
│     │                                                          │
│     ▼                                                          │
│  CX gate: (|00⟩₁₂ + |11⟩₁₂)/√2 = |Φ⁺⟩₁₂                      │
│                                                                 │
│  ┌───┐     ┌─┴─┐                                              │
│  │ H ├─────┤ X ├                                              │
│  └───┘     └───┘                                              │
│                                                                 │
│  Result: Entangled Bell state |Φ⁺⟩₁₂                         │
└─────────────────────────────────────────────────────────────────┘
```

This quantum circuit diagram shows the **real quantum teleportation** implementation in EntangleMe. Each step represents actual quantum operations that would be performed on real quantum hardware! 