# EntangleMe 🌀  
> A messaging app using **Quantum Teleportation**

We built **EntangleMe** to explore how quantum teleportation could work as a message transfer system. It uses **Qiskit** to simulate teleporting qubit states and connects it to a simple web interface—where one user sends a bit and the other receives it.

---

## 🛠 Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Qiskit](https://img.shields.io/badge/Qiskit-6929C4?style=for-the-badge&logo=Qiskit&logoColor=white)
![Classiq](https://img.shields.io/badge/Classiq-3B3C36?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyBmaWxsPSJ3aGl0ZSIgdmlld0JveD0iMCAwIDUxMiA1MTIiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjUxMiIgaGVpZ2h0PSI1MTIiIGZpbGw9ImJsYWNrIiByeD0iMjUiLz48dGV4dCB4PSIxMjgiIHk9IjI4MCIgZm9udC1zaXplPSIyMDAiIGZpbGw9IndoaXRlIj5DQTwvdGV4dD48L3N2Zz4=)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)

---

## 🌐 Live Demo

- 🔗 **Frontend:** [https://entangleme.vercel.app/](https://entangleme.vercel.app/)
- 🔗 **Backend API:** [https://entangleme.onrender.com/](https://entangleme.onrender.com/)
- 📚 **API Documentation:** [https://entangleme.onrender.com/docs](https://entangleme.onrender.com/docs)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Git

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/dev-Ninjaa/EntangleMe.git
   cd EntangleMe
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python run.py
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Access the application**
   - Frontend: http://localhost:5173
   - Backend: http://localhost:8000
   - API Docs: http://localhost:8000/docs

---

## 🏭 Production Deployment

### Backend (Render)
- ✅ **Deployed:** [https://entangleme.onrender.com/](https://entangleme.onrender.com/)

### Frontend (Vercel)
- ✅ **Deployed:** [https://entangleme.vercel.app/](https://entangleme.vercel.app/)


### Environment Variables

**Backend (Render)**
```bash
HOST=0.0.0.0
PORT=8000
DEBUG=False
SECRET_KEY=your-super-secret-key
DATABASE_URL=your-database-url
REDIS_URL=your-redis-url
```

**Frontend (Vercel)**
```bash
VITE_API_URL=https://entangleme.onrender.com/api/v1
```

---

## Why EntangleMe Matters ? (🔅USP)

Entangleme isn't just a hackathon demo—it's a glimpse into the future of secure, low-latency, web-integrated quantum communication. Here's how:

### 1. Quantum-Resistant Messaging  
By transforming our simulated teleportation pipeline into a true QKD channel, Entangleme can use the randomly generated measurement outcomes as shared secret keys. After each teleportation, those key bits encrypt classical payloads—guaranteeing that any eavesdropping attempt is immediately detectable. The result? Provably secure chat that classical encryption alone cannot match.

### 2. Hybrid Quantum-Classical Workflows  
Not all users have direct access to quantum hardware. Entangleme's modular FastAPI and frontend architecture can be deployed as serverless functions or at the network edge, running lightweight quantum simulations close to the user. This hybrid approach slashes round-trip latency, demonstrating how quantum-enhanced services can be woven into existing cloud-native infrastructures today.

### 3. On-Ramp to the Quantum Internet  
As quantum repeaters and entanglement distribution networks become available, Entangleme's "simulator-swap" design lets us replace Qiskit's backend with live hardware with minimal code changes. That means our browser-first UI and teleportation endpoint become an early user interface for the emerging quantum internet—empowering developers and researchers to experiment with real entangled links and build the next generation of networked applications.

---

## ⚙️ How It Works (TL;DR)

1. **Qiskit:** Simulates quantum teleportation of `0` or `1` using IBM Quantum.
2. **FastAPI:** RESTful API endpoints for quantum operations and chat.
3. **React + TypeScript:** Modern frontend with real-time chat interface.
4. **Quantum Teleportation:** Users can send bits (0/1) via quantum teleportation.
5. **Real-time Chat:** WebSocket-based messaging with quantum state visualization.

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

- 🔗 **Prototype Website:** [https://entangleme.vercel.app/](https://entangleme.vercel.app/)
- 📽 **Demo Video:** [YouTube / Loom Link]
- 🚀 **Devpost Project:** [https://devpost.com/software/entangleme](https://devpost.com/software/entangleme)
- 🎯 **Hackathon:** [https://cqhack25.devpost.com/](https://cqhack25.devpost.com/)
- 📄 **View Full Documentation:** [docs/docs.md](docs/docs.md)

---

## 👨‍💻 Hawkeye Team Members

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
- 🔧 [FastAPI Documentation](https://fastapi.tiangolo.com/)
- ☁️ [Render Deployment Guide](https://render.com/docs/deploy-flask)

---

> Built with ❤️ + 🧠 + ⚛️ during CQHack25
