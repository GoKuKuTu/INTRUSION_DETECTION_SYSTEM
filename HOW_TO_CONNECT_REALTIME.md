# How to Connect and Use Real-Time IDS

## 🔌 Step-by-Step Connection Guide

### Step 1: Ensure Both Servers Are Running

**Backend Server:**
```bash
cd network-anomaly-detection
python simple_realtime_server.py
```
Should show: `Starting server on http://0.0.0.0:5000`

**Frontend Server:**
```bash
cd web
npm run dev
```
Should show: `Local: http://localhost:5173/`

### Step 2: Open the Application

1. Open your web browser
2. Navigate to: **http://localhost:5173**
3. Wait for the page to fully load

### Step 3: Navigate to Real-Time Dashboard

1. Scroll down the page
2. Find the **"Real-Time Intrusion Detection"** section
3. You should see the dashboard with connection controls

### Step 4: Check Connection Status

Look for the connection indicator:
- **🟢 Green "Connected"** = Success! Socket.IO is connected
- **🔴 Red "Disconnected"** = Connection issue (see troubleshooting below)

### Step 5: Start Real-Time Monitoring

1. Once you see **"Connected"** status (green)
2. Click the **"Start Monitoring"** button
3. The status will change to **"Monitoring Active"**
4. You'll start seeing live network traffic analysis!

## 🔍 Verify Connection is Working

### Method 1: Browser Console (Recommended)

1. Press **F12** to open DevTools
2. Go to **Console** tab
3. Look for these messages:
   ```
   🔌 Initializing Socket.IO connection to: http://localhost:5000
   ✅ Socket.IO Connected! ID: abc123...
   📨 Server connected message: {message: "Connected to Real-Time IDS", status: "connected"}
   ```

### Method 2: Network Tab

1. Press **F12** → **Network** tab
2. Filter by **"WS"** (WebSocket)
3. Look for `socket.io` connection
4. Status should be **"101 Switching Protocols"**

### Method 3: Backend Health Check

Open in browser: **http://localhost:5000/health**

Should return:
```json
{
  "status": "healthy",
  "message": "API is running",
  "ids_running": false,
  "model_loaded": false
}
```

## 🎯 What You'll See When Connected

### Dashboard Elements:

1. **Connection Status**
   - Shows "Connected" (green) or "Disconnected" (red)
   - Displays active flow count

2. **Statistics Cards**
   - Total Flows
   - Normal Flows
   - Attack Flows
   - Active Flows

3. **Control Buttons**
   - **Start Monitoring** - Begins real-time analysis
   - **Stop Monitoring** - Stops analysis

4. **Live Data Panels**
   - **Recent Attacks** - Shows detected intrusions
   - **Live Predictions** - Streams real-time flow analysis

## 🐛 Troubleshooting "Disconnected" Status

### Issue 1: Backend Not Running

**Symptoms:**
- Status shows "Disconnected"
- Console shows "Connection refused"

**Solution:**
```bash
cd network-anomaly-detection
python simple_realtime_server.py
```

### Issue 2: CORS Error

**Symptoms:**
- Console shows CORS error
- Connection fails immediately

**Solution:**
- Backend already has CORS enabled
- Check backend is running on port 5000
- Verify frontend is on port 5173

### Issue 3: Socket.IO Not Connecting

**Symptoms:**
- No connection messages in console
- Status stuck on "Disconnected"

**Solution:**
1. Check backend: http://localhost:5000/health
2. Check Socket.IO endpoint: http://localhost:5000/socket.io/
3. Refresh browser (F5)
4. Check browser console for specific errors

### Issue 4: Port Already in Use

**Symptoms:**
- Backend won't start
- Error: "Address already in use"

**Solution:**
```powershell
# Find process using port 5000
netstat -ano | findstr :5000

# Kill the process (replace PID with actual process ID)
taskkill /PID <PID> /F
```

## ✅ Quick Connection Test

Run this in browser console (F12):
```javascript
// Test Socket.IO connection
const socket = io('http://localhost:5000');
socket.on('connect', () => console.log('✅ Connected!'));
socket.on('disconnect', () => console.log('❌ Disconnected'));
socket.on('connect_error', (err) => console.error('❌ Error:', err));
```

## 🚀 Full Real-Time Workflow

1. **Start Backend**
   ```bash
   cd network-anomaly-detection
   python simple_realtime_server.py
   ```

2. **Start Frontend**
   ```bash
   cd web
   npm run dev
   ```

3. **Open Browser**
   - Go to: http://localhost:5173
   - Scroll to Real-Time Dashboard

4. **Verify Connection**
   - Check status shows "Connected" (green)
   - Check browser console (F12) for connection messages

5. **Start Monitoring**
   - Click "Start Monitoring" button
   - Watch live predictions stream in

6. **View Results**
   - See statistics update in real-time
   - View detected attacks in "Recent Attacks" panel
   - Monitor live predictions in "Live Predictions" stream

## 📊 Expected Behavior

### When Connected:
- ✅ Status indicator: Green "Connected"
- ✅ "Start Monitoring" button: Enabled
- ✅ Console shows: "Socket.IO Connected!"
- ✅ No error messages in console

### When Monitoring:
- ✅ Status: "Monitoring Active"
- ✅ Statistics updating in real-time
- ✅ Predictions streaming in "Live Predictions" panel
- ✅ Attacks appearing in "Recent Attacks" panel

## 🎓 Understanding the Connection

The real-time connection uses **WebSocket** (via Socket.IO) for:
- **Bidirectional communication** between frontend and backend
- **Real-time updates** without page refresh
- **Low latency** for instant predictions
- **Automatic reconnection** if connection drops

## 💡 Tips

1. **Keep browser console open** (F12) to see connection status
2. **Check backend terminal** for server logs
3. **Refresh browser** (F5) if connection seems stuck
4. **Verify both servers** are running before connecting

---

**Need Help?** Check the browser console (F12) for specific error messages and share them for troubleshooting.

