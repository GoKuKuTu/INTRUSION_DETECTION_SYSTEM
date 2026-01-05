# Connection Troubleshooting - Still Shows "Disconnected"

## Current Status
Dashboard shows: **"Disconnected"** (red status)

## Quick Fix Steps

### Step 1: Verify Backend is Running
```powershell
# Check if backend responds
Invoke-WebRequest -Uri "http://localhost:5000/health"
```

**Expected:** `{"status":"healthy",...}`

**If not running, start it:**
```bash
cd network-anomaly-detection
python simple_realtime_server.py
```

### Step 2: Hard Refresh Browser
1. **Press Ctrl+Shift+R** (hard refresh) or **Ctrl+F5**
2. This clears cache and reloads all JavaScript
3. Check console again (F12)

### Step 3: Check Browser Console
Press **F12** → **Console** tab

**Look for:**
- ✅ `Socket.IO Connected! ID: ...` = Success!
- ❌ `WebSocket connection failed` = Connection issue
- ❌ `Connection refused` = Backend not running

### Step 4: Test Socket.IO Manually
In browser console (F12), run:
```javascript
// Test connection
const testSocket = io('http://localhost:5000');
testSocket.on('connect', () => {
    console.log('✅ MANUAL TEST: Connected!');
    alert('Connection successful!');
});
testSocket.on('connect_error', (err) => {
    console.error('❌ MANUAL TEST Error:', err);
});
```

### Step 5: Check Network Tab
1. Press **F12** → **Network** tab
2. Filter by **"WS"** (WebSocket)
3. Look for `socket.io` connection
4. Status should be **"101 Switching Protocols"**

## Common Issues

### Issue 1: Backend Not Running
**Solution:** Start backend server

### Issue 2: Browser Cache
**Solution:** Hard refresh (Ctrl+Shift+R)

### Issue 3: Port Mismatch
**Solution:** Already fixed - frontend uses port 5000

### Issue 4: React StrictMode Double Render
**Solution:** Already fixed - removed forceNew

### Issue 5: CORS Blocking
**Solution:** Backend has CORS enabled, but check browser console

## Manual Connection Test

Run this in browser console:
```javascript
// Clear any existing connections
if (window.testSocket) window.testSocket.disconnect();

// Create new connection
window.testSocket = io('http://localhost:5000', {
    transports: ['websocket', 'polling'],
    reconnection: true
});

window.testSocket.on('connect', () => {
    console.log('✅ TEST: Connected! ID:', window.testSocket.id);
    document.querySelector('[class*="Disconnected"]')?.textContent = 'Connected';
});

window.testSocket.on('connect_error', (err) => {
    console.error('❌ TEST Error:', err);
});
```

## Expected Console Output (Success)

```
🔧 API_BASE configured as: http://localhost:5000
🔧 Connecting to backend on port 5000
🔌 Initializing Socket.IO connection to: http://localhost:5000
✅ Socket.IO Connected! ID: abc123...
📨 Server connected message: {message: "Connected to Real-Time IDS", status: "connected"}
```

## If Still Not Working

1. **Check backend terminal** - Look for connection logs
2. **Check browser console** - Look for specific errors
3. **Try different browser** - Rule out browser-specific issues
4. **Check firewall** - Ensure ports 5000 and 5173 are not blocked

---

**Most Important:** Hard refresh the browser (Ctrl+Shift+R) after code changes!

