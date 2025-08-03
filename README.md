# EntangleMe 🌀  
> A messaging app using **Quantum Teleportation**

We built **Entangleme** to explore how quantum teleportation could work as a message transfer system. It uses **Qiskit** to simulate teleporting qubit states and connects it to a simple web interface—where one user sends a bit and the other receives it.

---

## 🛠 Tech Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Qiskit](https://img.shields.io/badge/Qiskit-6929C4?style=for-the-badge&logo=Qiskit&logoColor=white)
![Classiq](https://img.shields.io/badge/Classiq-3B3C36?style=for-the-badge&logo=data:image/svg+xml;base64,PHN2ZyBmaWxsPSJ3aGl0ZSIgdmlld0JveD0iMCAwIDUxMiA1MTIiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PHJlY3Qgd2lkdGg9IjUxMiIgaGVpZ2h0PSI1MTIiIGZpbGw9ImJsYWNrIiByeD0iMjUiLz48dGV4dCB4PSIxMjgiIHk9IjI4MCIgZm9udC1zaXplPSIyMDAiIGZpbGw9IndoaXRlIj5DQTwvdGV4dD48L3N2Zz4=)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=for-the-badge&logo=html5&logoColor=white)
![Render](https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=black)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)

---

## ⚙️ How It Works (TL;DR)

1. **Qiskit:** Simulates quantum teleportation of `0` or `1` using IBM Quantum.
2. **Python Function:** Wraps teleportation into `quantum_teleportation(input_state)`.
3. **Flask API:** Simple POST endpoint to trigger teleportation and return result.
4. **Frontend:** Plain HTML+JS UI where you select a bit and receive the output.
5. **Deployment:** Backend on **Render**, frontend on **Vercel**—works anywhere!

---
## ⚛️ We Also Used: Classiq to Auto-Generate Teleportation Circuits

To simplify or scale the quantum backend, we explored using **Classiq**, a high-level quantum algorithm synthesis platform. Instead of building the quantum circuit manually, Classiq lets us define **intent**, and it builds the optimized circuit for us.

---
## 🌐 Links

- 🔗 **Prototype Website:** [your-site-url.vercel.app]
- 📽 **Demo Video:** [YouTube / Loom Link]
- 🚀 **Devpost Project:** [https://devpost.com/software/entangleme]
- 🎯 **Hackathon:** [https://cqhack25.devpost.com/]

---

## 👨‍💻 Team Members

| Role        | Name         | GitHub / Profile Link |
|-------------|--------------|------------------------|
| 🧠 Lead     | Md Athar Jamal Makki  | [@atharhive]       |
| 🎨 Frontend | Akshad Jogi  | [@akshad-exe]     |
| 🛠 Backend  | Ayush Sarkar  | [@dev-Ninjaa]      |

---

## 🧠 Core Concept

We followed actual quantum teleportation principles:
> Entangle → Encode → Measure → Send Classical Bits → Apply Corrections

This is the same foundation used in **quantum internet** and **secure quantum communication**.

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
