# EntangleMe 🌀  
> A messaging app using **Quantum Teleportation**

We built **EntangleMe** to explore how quantum teleportation could work as a message transfer system. It uses **Qiskit** to simulate teleporting qubit states and connects it to a simple web interface—where one user sends a bit and the other receives it.

---

## 🛠 Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Qiskit](https://img.shields.io/badge/Qiskit-6929C4?style=for-the-badge&logo=Qiskit&logoColor=white)
![Classiq](https://img.shields.io/badge/Classiq-3B3C36?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyBmaWxsPSJ3aGl0ZSIgdmlld0JveD0iMCAwIDUxMiA1MTIiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjUxMiIgaGVpZ2h0PSI1MTIiIGZpbGw9ImJsYWNrIiByeD0iMjUiLz48dGV4dCB4PSIxMjgiIHk9IjI4MCIgZm9udC1zaXplPSIyMDAiIGZpbGw9IndoaXRlIj5DQTwvdGV4dD48L3N2Zz4=)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)

---

## Why EntangleMe Matters ? (🔅USP)

Entangleme isn’t just a hackathon demo—it’s a glimpse into the future of secure, low-latency, web-integrated quantum communication. Here’s how:

### 1. Quantum-Resistant Messaging  
By transforming our simulated teleportation pipeline into a true QKD channel, Entangleme can use the randomly generated measurement outcomes as shared secret keys. After each teleportation, those key bits encrypt classical payloads—guaranteeing that any eavesdropping attempt is immediately detectable. The result? Provably secure chat that classical encryption alone cannot match.

### 2. Hybrid Quantum-Classical Workflows  
Not all users have direct access to quantum hardware. Entangleme’s modular Flask API and frontend architecture can be deployed as serverless functions or at the network edge, running lightweight quantum simulations close to the user. This hybrid approach slashes round-trip latency, demonstrating how quantum-enhanced services can be woven into existing cloud-native infrastructures today.

### 3. On-Ramp to the Quantum Internet  
As quantum repeaters and entanglement distribution networks become available, Entangleme’s “simulator-swap” design lets us replace Qiskit’s backend with live hardware with minimal code changes. That means our browser-first UI and teleportation endpoint become an early user interface for the emerging quantum internet—empowering developers and researchers to experiment with real entangled links and build the next generation of networked applications.

---

## ⚙️ How It Works (TL;DR)

1. **Qiskit:** Simulates quantum teleportation of `0` or `1` using IBM Quantum.
2. **Python Function:** Wraps teleportation into `quantum_teleportation(input_state)`.
3. **Flask API:** Simple POST endpoint to trigger teleportation and return result.
4. **Frontend:** Plain HTML+JS UI where you select a bit and receive the output.
5. **Deployment:** Backend on **Render**, frontend on **Vercel**—works anywhere!

---
## 🧠 Core Concept

We followed actual quantum teleportation principles:
> Entangle → Encode → Measure → Send Classical Bits → Apply Corrections

This is the same foundation used in **quantum internet** and **secure quantum communication**.

---

## ⚛️ We Also Used: Classiq to Auto-Generate Teleportation Circuits

To simplify or scale the quantum backend, we explored using **Classiq**, a high-level quantum algorithm synthesis platform. Instead of building the quantum circuit manually, Classiq lets us define **intent**, and it builds the optimized circuit for us.

---
## 🌐 Links

- 🔗 **Prototype Website:** [your-site-url.vercel.app]
- 📽 **Demo Video:** [YouTube / Loom Link]
- 🚀 **Devpost Project:** [https://devpost.com/software/entangleme]
- 🎯 **Hackathon:** [https://cqhack25.devpost.com/]
- 📄 **View Full Documentation:** (https://github.com/dev-Ninjaa/EntangleMe/blob/main/docs.md)


---

## 👨‍💻 Team Members

| Role        | Name         | GitHub / Profile Link |
|-------------|--------------|------------------------|
| 🧠 Lead     | Md Athar Jamal Makki  | [@atharhive](https://github.com/atharhive)       |
| 🎨 Frontend | Akshad Jogi  | [@akshad-exe](https://github.com/akshad-exe)     |
| 🛠 Backend  | Ayush Sarkar  | [@dev-Ninjaa](https://github.com/dev-Ninjaa)      |

---

## 📚 Resources

- 📘 [Qiskit Teleportation Notebook](https://github.com/qiskit-community/qiskit-community-tutorials/blob/master/Coding_With_Qiskit/ep5_Quantum_Teleportation.ipynb)
- ▶️ [Qiskit YouTube Tutorial](https://www.youtube.com/watch?v=mMwovHK2NrE)
- ⚛️ [Classiq Docs](https://docs.classiq.io/)
- 🌐 [IBM Quantum Lab](https://quantum-computing.ibm.com/)
- 🔧 [Flask Quickstart](https://flask.palletsprojects.com/en/3.0.x/quickstart/)
- ☁️ [Render Deployment Guide](https://render.com/docs/deploy-flask)

---

> Built with ❤️ + 🧠 + ⚛️ during CQHack25
