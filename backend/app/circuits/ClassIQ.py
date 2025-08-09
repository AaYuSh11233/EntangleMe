'''
from classiq import Client 
from classiq.qmod import Qmod

# Initialize Classiq Client
client = Client()

# Define a simple 2-qubit quantum circuit
qmod = Qmod()
q0 = qmod.qbit()
q1 = qmod.qbit()

# Example: Apply a Hadamard gate to q0 and CNOT between q0 and q1
qmod.h(q0)
qmod.cx(q0, q1)

# Compile the circuit
circuit = client.compile(qmod)

# Print the circuit
print(circuit)

# (Optional) Execute on IonQ backend if configured
# execution_result = client.execute(circuit, target="ionq.simulator")
# print(execution_result)

'''