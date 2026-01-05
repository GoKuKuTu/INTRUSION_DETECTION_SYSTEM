# Fix: "Disconnected" Status Issue

## Problem
The real-time dashboard shows "Disconnected" because the backend server is not starting properly.

## Root Cause
The backend is crashing during startup due to:
1. TensorFlow import errors (numpy version conflict)
2. Missing dependencies
3. Import order issues

## ✅ Solution Applied

I've made TensorFlow imports **lazy** (only loaded when needed) to prevent startup crashes.

## 🔧 Steps to Fix

### Option 1: Quick Fix (Recommended)
1. **Stop all running Python processes**:
   ```powershell
   Get-Process python | Stop-Process -Force
   ```

2. **Start backend with explicit model**:
   ```bash
   cd network-anomaly-detection
   python start_realtime_ids.py --model models/ml_best.pkl --model-type ml
   ```

3. **Wait 10-15 seconds**, then check:
   ```
   http://localhost:5000/health
   ```

4. **Refresh browser** (F5) to reconnect Socket.IO

### Option 2: Use Test Server (If main server fails)
```bash
cd network-anomaly-detection
python test_server_simple.py
```

This starts a minimal server to test Socket.IO connection.

## 🔍 Verify Connection

1. **Check Backend**:
   - Open: http://localhost:5000/health
   - Should return: `{"status":"healthy",...}`

2. **Check Browser Console** (F12):
   - Should see: `✅ Connected to real-time IDS`
   - If errors, they'll show here

3. **Check Socket.IO Endpoint**:
   - Open: http://localhost:5000/socket.io/
   - Should show Socket.IO handshake page

## 🐛 If Still Disconnected

### Check 1: Backend Process
```powershell
Get-Process python
```
Should show Python processes running.

### Check 2: Port Availability
```powershell
netstat -ano | findstr :5000
```
Should show Python process listening on port 5000.

### Check 3: Browser Console
1. Open DevTools (F12)
2. Go to Console tab
3. Look for Socket.IO errors
4. Common errors:
   - `Connection refused` → Backend not running
   - `CORS error` → Backend CORS not configured
   - `WebSocket failed` → Socket.IO not initialized

### Check 4: Network Tab
1. Open DevTools (F12)
2. Go to Network tab
3. Filter by "WS" (WebSocket)
4. Look for `socket.io` connection
5. Status should be "101 Switching Protocols"

## ✅ Expected Behavior

After fix:
- ✅ Backend responds to http://localhost:5000/health
- ✅ Browser console shows "Connected to real-time IDS"
- ✅ Dashboard shows "Connected" (green)
- ✅ "Start Monitoring" button is enabled

## 🚀 Next Steps

Once connected:
1. Click "Start Monitoring"
2. Watch for real-time predictions
3. See live network traffic analysis

---

**Note**: The TensorFlow import issue has been fixed by making imports lazy. The backend should now start successfully even if TensorFlow has version conflicts.

