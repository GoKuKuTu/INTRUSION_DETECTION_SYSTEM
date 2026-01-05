# Fix "Disconnected" Status - Step by Step

## 🔴 Current Issue
Your dashboard shows: **"Disconnected"** (red status)

## ✅ Quick Fix Steps

### Step 1: Verify Backend is Running

**Check if backend is running:**
```powershell
# In PowerShell, run:
Invoke-WebRequest -Uri "http://localhost:5000/health"
```

**Or open in browser:**
```
http://localhost:5000/health
```

**Expected response:**
```json
{"status":"healthy","message":"API is running",...}
```

### Step 2: If Backend is NOT Running

**Start the backend server:**
```bash
cd network-anomaly-detection
python simple_realtime_server.py
```

**You should see:**
```
Starting server on http://0.0.0.0:5000
Health check: http://localhost:5000/health
Socket.IO: ws://localhost:5000/socket.io/
```

### Step 3: Check Browser Console

1. **Press F12** in your browser
2. Go to **Console** tab
3. Look for these messages:

**✅ Good (Connected):**
```
🔌 Initializing Socket.IO connection to: http://localhost:5000
✅ Socket.IO Connected! ID: abc123...
```

**❌ Bad (Error):**
```
❌ Connection error: ...
Connection refused
CORS error
```

### Step 4: Refresh Browser

After backend is running:
1. **Refresh the page** (F5 or Ctrl+R)
2. Check console again
3. Status should change to "Connected" (green)

### Step 5: Test Socket.IO Connection

**In browser console (F12), run:**
```javascript
// Test connection
const testSocket = io('http://localhost:5000');
testSocket.on('connect', () => {
    console.log('✅ TEST: Connected!');
    document.querySelector('[class*="status"]').textContent = 'Connected';
});
testSocket.on('connect_error', (err) => {
    console.error('❌ TEST Error:', err);
});
```

## 🔍 Common Issues & Solutions

### Issue 1: Backend Not Running
**Symptom:** Console shows "Connection refused"
**Solution:** Start backend with `python simple_realtime_server.py`

### Issue 2: Wrong Port
**Symptom:** Connection to wrong URL
**Solution:** Check `API_BASE` in RealtimeDashboard.jsx (should be `http://localhost:5000`)

### Issue 3: CORS Error
**Symptom:** Console shows CORS error
**Solution:** Backend already has CORS enabled, restart backend

### Issue 4: Socket.IO Not Initialized
**Symptom:** No connection messages in console
**Solution:** Check if `socket.io-client` is installed: `cd web && npm install socket.io-client`

## 🎯 Expected Result

After fixing, you should see:
- ✅ **Green "Connected"** status (instead of red "Disconnected")
- ✅ Console shows: "Socket.IO Connected!"
- ✅ "Start Monitoring" button is enabled
- ✅ No red error messages in console

## 🚀 Quick Command Summary

```bash
# Terminal 1: Start Backend
cd network-anomaly-detection
python simple_realtime_server.py

# Terminal 2: Start Frontend (if not running)
cd web
npm run dev

# Browser:
# 1. Open http://localhost:5173
# 2. Press F12 → Console tab
# 3. Refresh page (F5)
# 4. Look for "Connected" status
```

---

**Most likely issue:** Backend server is not running. Start it with the command above!

