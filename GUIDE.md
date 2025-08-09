# 🌀 EntangleMe - Testing & Troubleshooting Guide

## 📋 **Table of Contents**
- [🎯 Quick Testing Guide](#-quick-testing-guide)
- [🐛 Common Issues & Solutions](#-common-issues--solutions)
- [🔧 Known Bugs & Workarounds](#-known-bugs--workarounds)
- [🚨 Critical Issues](#-critical-issues)
- [📹 Demo Videos](#-demo-videos)
- [🧪 Testing Scenarios](#-testing-scenarios)
- [🔍 Debug Information](#-debug-information)
- [🗄️ Database Management](#️-database-management)

---

## 🎯 **Quick Testing Guide**

### **1. Initial Setup Testing**

#### **Frontend Testing**
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Access the application
# Open: http://localhost:5173
```

#### **Backend Testing**
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the backend server
python run.py

# Access the API
# Open: https://entangleme.onrender.com/docs
```

---

## 🗄️ **Database Management**

### **Reset Database Endpoint**

**Endpoint**: `POST /reset-db`

**Usage**:
```bash
# Reset the entire database (DANGER: deletes all data!)
curl -X POST "https://entangleme.onrender.com/reset-db" \
  -H "Content-Type: application/json" \
  -d '{"confirmation": "yes"}'

# Check database status
curl "https://entangleme.onrender.com/db-status"
```

### **Database Status Endpoint**

**Endpoint**: `GET /db-status`

**Usage**:
```bash
# Get database status (JSON)
curl "https://entangleme.onrender.com/db-status"

# Get database status (HTML interface)
# Open: https://entangleme.onrender.com/db-status
```

### **Standalone HTML Tools**

**1. Reset Database Tool**:
- **Access**: https://entangleme.onrender.com/reset-db
- **Features**:
  - Type "yes" in the confirmation field
  - Click "Reset Database" button
  - Real-time validation
  - Loading states and success/error messages

**2. Database Status Tool**:
- **Access**: https://entangleme.onrender.com/db-status
- **Features**:
  - Real-time database status and information
  - Auto-refresh every 30 seconds
  - Visual representation of tables and record counts
  - Expandable table sections with actual data

---

## 🐛 **Common Issues & Solutions**

### **Issue 1: Buttons Not Clickable on First Load**

**Problem**: When you first enter the site, the "Get Started" and "Learn More" buttons may not be clickable.

**Solution**:
1. **Refresh the page** (Ctrl+F5 or Cmd+Shift+R)
2. If that doesn't work, clear browser cache and cookies
3. Try opening in an incognito/private window

---

### **Issue 2: Room Connection Problems**

**Problem**: Users may appear to be connected but are actually disconnected due to browser closure without proper cleanup.

**Solution**:
1. **Wait 5-10 minutes** for automatic cleanup
2. **Restart the backend server**
3. **Use database reset**: https://entangleme.onrender.com/reset-db

---

### **Issue 3: Quantum Teleportation Failures**

**Problem**: Quantum teleportation may fail or show incorrect results.

**Solution**:
1. **Check backend status**: https://entangleme.onrender.com/health
2. **Test quantum endpoint**:
   ```bash
   curl -X POST "https://entangleme.onrender.com/api/v1/quantum/teleport" \
        -H "Content-Type: application/json" \
        -d '{"classical_bit": 0}'
   ```

---

### **Issue 4: Real-time Updates Not Working**

**Problem**: Messages or status updates don't appear in real-time.

**Solution**:
1. Check network connection
2. Use Chrome, Firefox, or Edge (latest versions)
3. Clear browser cache and cookies
4. Try incognito mode

---

## 🔧 **Known Bugs & Workarounds**

### **Bug 1: Button Responsiveness**
- **Status**: Known Issue
- **Workaround**: Refresh page
- **Fix Status**: In Progress

### **Bug 2: User Session Cleanup**
- **Status**: Known Issue
- **Workaround**: Manual server restart or database reset
- **Fix Status**: Planned

### **Bug 3: Quantum Circuit Rendering**
- **Status**: Occasional
- **Workaround**: Refresh quantum dashboard
- **Fix Status**: Under Investigation

---

## 🚨 **Critical Issues**

### **Issue: User Session Persistence**

**Problem**: When users close their browsers without properly leaving rooms, they remain connected in the backend.

**Solution**:
1. **For Users**: Always click "Leave" before closing browser
2. **For Developers**: Use database reset at https://entangleme.onrender.com/reset-db

---

## 📹 **Demo Videos**

### **Video 1: Button Responsiveness Bug**

**Description**: This video demonstrates the button responsiveness bug and how to fix it.

<div style="position: relative; width: 100%; height: 0; padding-bottom: 56.25%;">
  <iframe 
    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" 
    src="https://www.youtube.com/embed/inEV_1-zT_E" 
    title="Button Responsiveness Bug Demo" 
    frameborder="0" 
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
    allowfullscreen>
  </iframe>
</div>

**Steps Shown**:
1. Initial page load with non-responsive buttons
2. Demonstration of the issue
3. Solution: Page refresh
4. Working buttons after refresh

---

### **Video 2: Room Connection Issues**

**Description**: This video shows the room connection problems and user session issues.

<div style="position: relative; width: 100%; height: 0; padding-bottom: 56.25%;">
  <iframe 
    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%;" 
    src="https://www.youtube.com/embed/dQw4w9WgXcQ" 
    title="Room Connection Issues Demo" 
    frameborder="0" 
    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
    allowfullscreen>
  </iframe>
</div>

**Steps Shown**:
1. User A joins the room
2. User B joins and connects with User A
3. User A properly leaves using the "Leave" button
4. User B closes browser without leaving
5. User C tries to join but gets connected to User B (who's offline)
6. Demonstration of the cleanup issue

---

## 🧪 **Testing Scenarios**

### **Scenario 1: Basic Functionality Test**

**Steps**:
1. Open application in browser
2. Click "Get Started" → Should open username dialog
3. Enter username (3+ characters) → Should join room
4. Wait for second user or open second browser tab
5. Send quantum bit (0 or 1) → Should teleport successfully
6. Verify quantum visualization appears

**Expected Results**:
- ✅ All buttons responsive
- ✅ Username dialog appears
- ✅ Room joining works
- ✅ Quantum teleportation successful
- ✅ Visualization displays correctly

### **Scenario 2: Error Handling Test**

**Steps**:
1. Enter username < 3 characters → Should show error
2. Try to join with existing username → Should handle gracefully
3. Close browser during active session → Should cleanup properly
4. Test with slow network → Should show loading states

### **Scenario 3: Multi-User Test**

**Steps**:
1. Open application in two browser windows
2. Join with different usernames
3. Test message exchange
4. Test quantum teleportation
5. Test user leaving behavior

### **Scenario 4: Database Management Test**

**Steps**:
1. Visit https://entangleme.onrender.com/db-status
2. Check database status and tables
3. Visit https://entangleme.onrender.com/reset-db
4. Test database reset functionality

---

## 🔍 **Debug Information**

### **Frontend Debug**

**Browser Console**:
```javascript
// Check if React is loaded
console.log('React version:', React.version);

// Check if API is accessible
fetch('https://entangleme.onrender.com/health')
  .then(response => response.json())
  .then(data => console.log('API Status:', data))
  .catch(error => console.error('API Error:', error));
```

### **Backend Debug**

**API Testing**:
```bash
# Test health endpoint
curl https://entangleme.onrender.com/health

# Test quantum endpoint
curl -X POST "https://entangleme.onrender.com/api/v1/quantum/teleport" \
     -H "Content-Type: application/json" \
     -d '{"classical_bit": 1}'

# Test database status
curl https://entangleme.onrender.com/db-status

# Test database reset (DANGER!)
curl -X POST "https://entangleme.onrender.com/reset-db" \
     -H "Content-Type: application/json" \
     -d '{"confirmation": "yes"}'
```

### **Database Debug**

**Check Database Status**:
```bash
# Using curl
curl https://entangleme.onrender.com/db-status

# Using browser
# Open: https://entangleme.onrender.com/db-status
```

**Reset Database**:
```bash
# Using curl
curl -X POST "https://entangleme.onrender.com/reset-db" \
     -H "Content-Type: application/json" \
     -d '{"confirmation": "yes"}'

# Using browser
# Open: https://entangleme.onrender.com/reset-db
```

---

## 📞 **Support & Contact**

### **Getting Help**

1. **Check This Guide**: Review the sections above for common solutions
2. **GitHub Issues**: Create an issue on the [GitHub repository](https://github.com/dev-Ninjaa/EntangleMe)
3. **Team Contact**: Reach out to team members:
   - **Lead**: [@atharhive](https://github.com/atharhive)
   - **Frontend**: [@akshad-exe](https://github.com/akshad-exe)
   - **Backend**: [@dev-Ninjaa](https://github.com/dev-Ninjaa)

### **Reporting Issues**

When reporting issues, please include:
1. **Browser**: Chrome/Firefox/Safari/Edge version
2. **Operating System**: Windows/Mac/Linux
3. **Steps to Reproduce**: Detailed steps
4. **Expected vs Actual Behavior**: What you expected vs what happened
5. **Console Logs**: Any error messages from browser console
6. **Screenshots/Videos**: Visual evidence if possible

---

## 🎯 **Quick Troubleshooting Checklist**

- [ ] **Buttons not working** → Refresh page
- [ ] **Can't join room** → Check if room is full or restart server
- [ ] **Quantum teleportation fails** → Check backend status
- [ ] **Real-time updates not working** → Check network and browser
- [ ] **User appears online but offline** → Wait 5-10 minutes or restart server
- [ ] **Visualization not showing** → Refresh quantum dashboard
- [ ] **Database issues** → Use https://entangleme.onrender.com/db-status or reset database
- [ ] **General issues** → Clear cache and cookies, try incognito mode

---

> **💡 Pro Tip**: Always use the "Leave" button before closing your browser to avoid session issues!

> **🔧 Developer Note**: This guide will be updated as issues are resolved and new features are added.
