# Entangleme 🌀

A simple messaging app built using Quantum Teleportation.

We made this during a hackathon to show how quantum teleportation can be turned into a working message transfer system. The idea is simple: use **Qiskit** to simulate teleporting qubit states and connect that to a web UI where one person sends a bit and the other receives it.

---

## 🛠️ Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Qiskit](https://img.shields.io/badge/Qiskit-6929C4?style=for-the-badge&logo=Qiskit&logoColor=white)
![Classiq](https://img.shields.io/badge/Classiq-3B3C36?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyBmaWxsPSJ3aGl0ZSIgdmlld0JveD0iMCAwIDUxMiA1MTIiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjUxMiIgaGVpZ2h0PSI1MTIiIGZpbGw9ImJsYWNrIiByeD0iMjUiLz48dGV4dCB4PSIxMjgiIHk9IjI4MCIgZm9udC1zaXplPSIyMDAiIGZpbGw9IndoaXRlIj5DQTwvdGV4dD48L3N2Zz4=)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)

---

## 🔧 How We Built It (Step-by-Step)

1.  **Ran the Quantum Teleportation Code**
    * We started with this [Qiskit notebook](https://github.com/qiskit-community/qiskit-community-tutorials/blob/master/Coding_With_Qiskit/ep5_Quantum_Teleportation.ipynb).
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
## ⚛️ We Also Used: Classiq to Auto-Generate Teleportation Circuits

To simplify or scale the quantum backend, we explored using **Classiq**, a high-level quantum algorithm synthesis platform. Instead of building the quantum circuit manually, Classiq lets us define **intent**, and it builds the optimized circuit for us.

### 🔄 Why Use Classiq?

| Without Classiq          | With Classiq                             |
|--------------------------|------------------------------------------|
| Manually define circuit  | Auto-generate from high-level model      |
| Qiskit-specific          | Exportable to Qiskit or other platforms  |
| Static input             | Easily support arbitrary qubit states    |



## 🧪 Real-World Application

We actually built this messaging app—**Entangleme**—using real quantum teleportation logic (simulated via Qiskit). While it doesn't send actual qubits over a network (since we're using simulators), the message still follows the same principle:

**Entangle two qubits → encode → Bell measurement → send classical bits → apply corrections.**

This is the exact foundation of real quantum communication systems and quantum internet research. 

## 🔑 Key Resources

* **Qiskit & Quantum Computing**
    * [Qiskit Teleportation Tutorial](https://www.youtube.com/watch?v=mMwovHK2NrE)
    * [IBM Quantum Lab](https://quantum-computing.ibm.com/) (for running Python/Qiskit online)
 
* **Classiq (Circuit Generation)**
    * [Classiq Docs](https://docs.classiq.io/)
    * [Classiq Platform](https://platform.classiq.io/)
    * [Classiq API Key Setup](https://docs.classiq.io/docs/quick-start/authentication)

* **Web Development: Backend (Flask)**
    * [Flask Documentation: A Minimal Application](https://flask.palletsprojects.com/en/3.0.x/quickstart/#a-minimal-application)
    * [Deploying Flask Apps on Render](https://render.com/docs/deploy-flask)

* **Web Development: Frontend (HTML/React)**
    * [HTML Fetch API Documentation (MDN)](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
    * [React Docs: Fetching Data](https://react.dev/learn/synchronizing-with-effects#fetching-data)
