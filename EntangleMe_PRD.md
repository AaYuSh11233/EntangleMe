# 📄 Product Requirements Document (PRD)

## EntangleMe: Quantum-Inspired Chat Web App

---

## ✨ Core Idea

EntangleMe is a quantum-inspired chat web app that allows two users to join a temporary chat room and send classical bits (0 or 1) to each other. The backend simulates quantum teleportation using Qiskit. No messages or sessions are stored—refreshing the browser wipes everything.

---

## 🎯 Goals

- Allow two users to enter their usernames and join a temporary room
- Enable them to send 0 or 1 to each other
- Simulate teleportation using a quantum backend
- Ensure messages are temporary (disappear on refresh)
- Easy to demo — fully local, no database or auth

---

## 🧩 Tech Stack

**Frontend**:
- HTML + CSS + JavaScript (Vanilla JS for simplicity)
- Optionally React

**Backend**:
- Flask (Python)
- Qiskit (to simulate teleportation logic)
- Server memory (dicts/variables) for temporary storage

**API**:
- Axios / fetch() for frontend requests to backend

---

## 🔐 Storage & State

- No database
- No cookies, localStorage, or sessions
- State only in RAM (lost on refresh)
- Frontend remembers only in JS variables

---

## 🖼 App Flow & Pages

**Login Page**:
- User enters a username
- Joins hardcoded room (e.g., `entangle-room`)
- When both users have joined, they are taken to the chat room

**Chat Room Page**:
- Header: Room Name (e.g., Entangle Room)
- Username shown at top
- Bit buttons: “Send 0” and “Send 1”
- Message log showing:
  - Who sent the bit
  - Bit value
  - Timestamp
- Leave Room button (clears session and returns to login)

**Example UI**:
```
┌──────────────────────────────┐
│ Room: Entangle Room         │
│ Logged in as: Ayush         │
├──────────────────────────────┤
│ ▸ Ayush sent 0 (12:04 PM)   │
│ ▸ Rex received 0 (12:04 PM) │
├──────────────────────────────┤
│ [Send 0] [Send 1]           │
│ [Leave Room]                │
└──────────────────────────────┘
```

---

## 📤 API Endpoints

**POST /join**  
Request:
```json
{ "username": "Ayush" }
```
Response:
```json
{ "status": "waiting" or "ready", "other_user": "Rex" }
```

**POST /send_bit**  
Request:
```json
{
  "username": "Ayush",
  "bit": 1
}
```
Response:
```json
{ "success": true }
```

**GET /messages**  
Response:
```json
[
  { "sender": "Ayush", "bit": 1, "timestamp": "12:04 PM" },
  { "sender": "Rex", "bit": 0, "timestamp": "12:05 PM" }
]
```

**POST /leave**  
Clears the user from memory and returns to login

---

## ⏲ Message Refresh Logic

- Frontend polls `/messages` every 2–3 seconds for updates
- All data is stored in memory (Python dictionaries)
- Refresh = data wiped

---

## ❌ Constraints

- No login/authentication
- No room selection
- No more than two users
- Hardcoded room: `entangle-room`
- No message persistence
- Only run on localhost or simple deployment (Render, Replit)

---

## 🧪 Test Cases

- ✅ User A joins → waits
- ✅ User B joins → both enter room
- ✅ Ayush sends 0 → Rex sees message
- ✅ Refresh → returns to login
- ✅ Sending anything other than 0 or 1 → shows error
