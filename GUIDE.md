# 🌀 EntangleMe - Testing & Troubleshooting Guide

## 📋 **Table of Contents**
- [🎯 Quick Testing Guide](#-quick-testing-guide)
- [🐛 Common Issues & Solutions](#-common-issues--solutions)
- [🔧 Known Bugs & Workarounds](#-known-bugs--workarounds)
- [🚨 Critical Issues](#-critical-issues)
- [📹 Demo Videos](#-demo-videos)
- [🧪 Testing Scenarios](#-testing-scenarios)
- [🔍 Debug Information](#-debug-information)

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
# Open: http://localhost:8000/docs
```

#### **New: Reset Database Endpoint**
We've added a new endpoint to reset the database programmatically:

**Endpoint**: `POST /reset-db`

**Usage with Request Body**:
```bash
# Reset the entire database (DANGER: deletes all data!)
# You must provide confirmation in the request body
curl -X POST "http://localhost:8000/reset-db" \
  -H "Content-Type: application/json" \
  -d '{"confirmation": "yes"}'

# Check database status
curl "http://localhost:8000/db-status"
```

**Response (Success)**:
```json
{
  "status": "success",
  "message": "Database reset completed successfully",
  "details": {
    "tables_dropped": true,
    "tables_recreated": true,
    "data_cleared": true
  },
  "warning": "All data has been permanently deleted!",
  "timestamp": "Reset completed at current time"
}
```

**Response (Confirmation Required)**:
```json
{
  "error": "Confirmation required",
  "message": "To reset the database, you must provide confirmation='yes' in the request body.",
  "example": {
    "confirmation": "yes"
  },
  "warning": "This operation will permanently delete all data!"
}
```

**Standalone HTML Tools**:
We've created standalone HTML pages that provide user-friendly interfaces for database management:

**1. Reset Database Tool** (`reset-database.html`):
- Open `reset-database.html` in your browser
- Type "yes" in the confirmation field
- Click "Reset Database" button

**2. Database Status Tool** (`database-status.html`):
- Open `database-status.html` in your browser or visit `/db-status` endpoint
- Real-time database status and information
- Auto-refresh every 30 seconds
- Visual representation of tables and record counts
- Environment and database information

**Custom API URL**: Add `?apiUrl=https://your-api-url.com` to the HTML file URL to use a different backend.

**Features**:
- ✅ Clean, modern UI with gradient design
- ✅ Real-time validation (button enables only when "yes" is typed)
- ✅ Loading states and success/error messages
- ✅ Mobile-responsive design
- ✅ Keyboard shortcuts (Ctrl+Enter to submit)
- ✅ Auto-focus on input field
- ✅ Warning messages and clear instructions
- ✅ Auto-refresh database status
- ✅ Visual table and record count display

**⚠️ Important Notes**:
- This endpoint will **permanently delete all data**
- **Confirmation required**: You must provide `{"confirmation": "yes"}` in the request body
- Use with extreme caution!
- Best used for development/testing environments
- No environment variables needed - just confirmation in request body

---

## 🐛 **Common Issues & Solutions**

### **Issue 1: Buttons Not Clickable on First Load**

**Problem**: When you first enter the site, the "Get Started" and "Learn More" buttons may not be clickable.

**Symptoms**:
- Buttons appear but don't respond to clicks
- No visual feedback when hovering or clicking
- Console may show errors

**Solution**:
1. **Refresh the page** (Ctrl+F5 or Cmd+Shift+R)
2. If that doesn't work, clear browser cache and cookies
3. Try opening in an incognito/private window

**Root Cause**: This is likely due to React component state initialization issues or JavaScript loading problems.

**Prevention**: The team is working on fixing this in the codebase.

---

### **Issue 2: Room Connection Problems**

**Problem**: Users may appear to be connected but are actually disconnected due to browser closure without proper cleanup.

**Scenario**:
```
User A (akshad) joins → User B (ayush) joins → Both connected
User A clicks "Leave" → Properly leaves (backend + browser)
User B closes browser → Still connected in backend
User C (athar) joins → Gets connected to User B (who's actually offline)
```

**Symptoms**:
- Users appear online but don't respond
- New users can't join rooms
- Inconsistent user status

**Solutions**:

#### **Temporary Fix**
1. **Manual Room Reset**:
   - Wait for 5-10 minutes (automatic cleanup)
   - Or restart the backend server

2. **Clear User Sessions**:
   - Delete browser cache and cookies
   - Try joining with a different username

#### **Permanent Fix (For Developers)**
```bash
# Restart backend server
cd backend
pkill -f "python run.py"
python run.py

# Or clear database (development only)
rm entangleme.db  # SQLite database
```

---

### **Issue 3: Quantum Teleportation Failures**

**Problem**: Quantum teleportation may fail or show incorrect results.

**Symptoms**:
- Error messages during teleportation
- Incorrect bit transmission
- Circuit visualization not working

**Solutions**:
1. **Check Backend Status**:
   - Ensure backend is running on `http://localhost:8000`
   - Check API documentation at `http://localhost:8000/docs`

2. **Verify Quantum Service**:
   ```bash
   # Test quantum endpoint
   curl -X POST "http://localhost:8000/api/v1/quantum/teleport" \
        -H "Content-Type: application/json" \
        -d '{"classical_bit": 0}'
   ```

3. **Check Qiskit Installation**:
   ```bash
   pip install qiskit qiskit-aer
   ```

---

### **Issue 4: Real-time Updates Not Working**

**Problem**: Messages or status updates don't appear in real-time.

**Symptoms**:
- Messages don't appear until page refresh
- User status not updating
- Room status stuck

**Solutions**:
1. **Check Network Connection**:
   - Ensure stable internet connection
   - Check if backend is accessible

2. **Browser Compatibility**:
   - Use Chrome, Firefox, or Edge (latest versions)
   - Disable ad-blockers temporarily

3. **Clear Browser Data**:
   - Clear cache and cookies
   - Try incognito mode

---

## 🔧 **Known Bugs & Workarounds**

### **Bug 1: Button Responsiveness**
- **Status**: Known Issue
- **Workaround**: Refresh page
- **Fix Status**: In Progress

### **Bug 2: User Session Cleanup**
- **Status**: Known Issue
- **Workaround**: Manual server restart
- **Fix Status**: Planned

### **Bug 3: Quantum Circuit Rendering**
- **Status**: Occasional
- **Workaround**: Refresh quantum dashboard
- **Fix Status**: Under Investigation

---

## 🚨 **Critical Issues**

### **Issue: User Session Persistence**

**Critical Problem**: When users close their browsers without properly leaving rooms, they remain connected in the backend, causing issues for new users.

**Impact**:
- Room capacity appears full when it's actually empty
- New users can't join rooms
- Inconsistent user experience

**Current Workaround**:
1. **For Users**:
   - Always click "Leave" before closing browser
   - Use the logout button properly
   - Wait 5-10 minutes if issues persist

2. **For Developers**:
   - Implement automatic session cleanup
   - Add heartbeat mechanism
   - Implement proper WebSocket cleanup

**Proposed Solution**:
```python
# Backend: Add automatic cleanup
import asyncio
from datetime import datetime, timedelta

async def cleanup_inactive_sessions():
    """Clean up inactive user sessions every 5 minutes"""
    while True:
        await asyncio.sleep(300)  # 5 minutes
        # Remove users inactive for more than 10 minutes
        cutoff_time = datetime.now() - timedelta(minutes=10)
        # Cleanup logic here
```

---

## 📹 **Demo Videos**

### **Video 1: Button Responsiveness Bug**

**Description**: This video demonstrates the button responsiveness bug and how to fix it.

**Video Link**: [Insert your video link here]

**Steps Shown**:
1. Initial page load with non-responsive buttons
2. Demonstration of the issue
3. Solution: Page refresh
4. Working buttons after refresh

**Duration**: ~2-3 minutes

---

### **Video 2: Room Connection Issues**

**Description**: This video shows the room connection problems and user session issues.

**Video Link**: [Insert your video link here]

**Steps Shown**:
1. User A joins the room
2. User B joins and connects with User A
3. User A properly leaves using the "Leave" button
4. User B closes browser without leaving
5. User C tries to join but gets connected to User B (who's offline)
6. Demonstration of the cleanup issue

**Duration**: ~3-4 minutes

---

## 🧪 **Testing Scenarios**

### **Scenario 1: Basic Functionality Test**

**Objective**: Verify basic application functionality

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

**Objective**: Test application error handling

**Steps**:
1. Enter username < 3 characters → Should show error
2. Try to join with existing username → Should handle gracefully
3. Close browser during active session → Should cleanup properly
4. Test with slow network → Should show loading states

**Expected Results**:
- ✅ Proper error messages
- ✅ Graceful error handling
- ✅ Loading states displayed
- ✅ No crashes or freezes

### **Scenario 3: Multi-User Test**

**Objective**: Test multi-user interactions

**Steps**:
1. Open application in two browser windows
2. Join with different usernames
3. Test message exchange
4. Test quantum teleportation
5. Test user leaving behavior

**Expected Results**:
- ✅ Both users can join
- ✅ Messages exchange properly
- ✅ Quantum teleportation works
- ✅ Leave functionality works

---

## 🔍 **Debug Information**

### **Frontend Debug**

**Browser Console**:
```javascript
// Check if React is loaded
console.log('React version:', React.version);

// Check if API is accessible
fetch('http://localhost:8000/api/v1/health')
  .then(response => response.json())
  .then(data => console.log('API Status:', data))
  .catch(error => console.error('API Error:', error));
```

**Network Tab**:
- Check for failed requests (red entries)
- Verify WebSocket connections
- Monitor API calls

### **Backend Debug**

**Server Logs**:
```bash
# Check backend logs
cd backend
python run.py

# Look for error messages in console output
```

**API Testing**:
```bash
# Test health endpoint
curl http://localhost:8000/api/v1/health

# Test quantum endpoint
curl -X POST "http://localhost:8000/api/v1/quantum/teleport" \
     -H "Content-Type: application/json" \
     -d '{"classical_bit": 1}'
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
- [ ] **General issues** → Clear cache and cookies, try incognito mode

---

> **💡 Pro Tip**: Always use the "Leave" button before closing your browser to avoid session issues!

> **🔧 Developer Note**: This guide will be updated as issues are resolved and new features are added.
