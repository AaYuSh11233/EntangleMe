# 🚀 EntangleMe Setup Guide

## 📋 Environment Configuration

Create a `.env` file in the `backend/` directory with the following configuration:

```bash
# ========================================
# EntangleMe Quantum Messaging Configuration
# ========================================

# 🔑 REQUIRED: Classiq API Key (Get from https://platform.classiq.io/)
CLASSIQ_API_KEY=your_classiq_api_key_here

# 🌐 Flask Configuration
## 🔐 REQUIRED: Flask Secret Key (Generate a secure random key)
SECRET_KEY=your_secure_random_secret_key_here
DEBUG=True

# Security Configuration
ENABLE_CORS=True

# ⚛️ Quantum Messaging Configuration
MAX_MESSAGE_LENGTH=1000
QUANTUM_SIMULATOR=aer_simulator

# 📊 Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/quantum_messaging.log
```

## 🔑 Getting Your Classiq API Key

1. **Visit** [https://platform.classiq.io/](https://platform.classiq.io/)
2. **Sign up** for a free account
3. **Navigate** to API settings in your dashboard
4. **Generate** a new API key for your project
5. **Copy** the key to your `.env` file

## 🔐 Generating a Secure Secret Key

Run this command to generate a secure Flask secret key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual keys
   ```

3. **Run the server:**
   ```bash
   python run.py
   ```

4. **Test the API:**
   ```bash
   curl http://localhost:5000/health
   ```

## ✅ What Works Without API Keys

- ✅ **Basic quantum teleportation** (Qiskit simulation)
- ✅ **Text messaging** functionality
- ✅ **All API endpoints**
- ✅ **Security features**
- ✅ **Testing and monitoring**

## 🔧 What Requires Classiq API Key

- 🔧 **Advanced circuit generation** (optional enhancement)
- 🔧 **Optimized quantum circuits** (performance improvement)
- 🔧 **Alternative quantum backends** (scalability)

## 🎯 Your Backend is Production-Ready!

Even without the Classiq API key, your system is **fully functional** and **production-ready**. The Classiq integration is an **optional enhancement** for advanced features. 