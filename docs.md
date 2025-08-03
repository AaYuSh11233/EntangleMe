# Entangleme 🌀

A simple messaging app built using Quantum Teleportation.

We made this during a hackathon to show how quantum teleportation can be turned into a working message transfer system. The idea is simple: use **Qiskit** to simulate teleporting qubit states and connect that to a web UI where one person sends a bit and the other receives it.

---

## 🛠️ Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Qiskit](https://img.shields.io/badge/Qiskit-6929C4?style=for-the-badge&logo=Qiskit&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)

---

## 🔧 How We Built It (Step-by-Step)

1.  **Ran the Quantum Teleportation Code**
    * We started with this [Qiskit notebook](https://qiskit.org/textbook/ch-algorithms/teleportation.html).
    * Ran it on **IBM Quantum Lab**.
    * Understood how entanglement, encoding, Bell measurement, classical bits, and correction gates work.
    * Tried changing input qubit states manually ($|0\rangle$, $|1\rangle$) to see the output.

2.  **Turned That Into a Function**
    * We took the teleportation logic and wrapped it into a Python function:
      ```python
      def quantum_teleportation(input_state: str) -> dict:
          # Build and simulate teleportation circuit
          # Return classical bits and receiver's qubit state
      ```
    * This function handles all quantum steps and works for "0" or "1" as input.

3.  **Created a Flask API**
    * Set up a minimal **Flask** server with one endpoint:
      ```
      POST /teleport
      {
        "state": "0"  // or "1"
      }
      ```
    * The endpoint runs `quantum_teleportation()` and sends back the teleported result.
    * This acts as the backend between the frontend and **Qiskit**.

4.  **Built a Simple Frontend**
    * Used plain **HTML + JS** for speed.
    * The UI has two boxes: **Sender** and **Receiver**.
    * The sender selects `0` or `1` and hits "Send."
    * JS uses `fetch()` to call the Flask API.
    * The receiver sees the classical bits and the output state.

5.  **Connected Everything Locally**
    * Ran the Flask backend on `localhost:5000`.
    * Opened the frontend in a browser.
    * Typed in the input → got the output from the simulated quantum teleportation.

6.  **Deployed the Full Stack**
    * **Backend (Flask):** Deployed on **Render**.
    * **Frontend:** Deployed on **Vercel**.
    * The frontend `fetch()` URL now points to the live backend.
    * Works from any device—no setup needed!

---

## 🧪 Real-World Application

We actually built this messaging app—**Entangleme**—using real quantum teleportation logic (simulated via Qiskit). While it doesn't send actual qubits over a network (since we're using simulators), the message still follows the same principle:

**Entangle two qubits → encode → Bell measurement → send classical bits → apply corrections.**

This is the exact foundation of real quantum communication systems and quantum internet research.
