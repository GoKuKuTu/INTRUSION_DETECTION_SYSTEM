# Starting the Real-Time IDS System

## 🚀 Quick Start Commands

### Option 1: Start Backend (Terminal 1)
```bash
cd network-anomaly-detection
python start_realtime_ids.py
```

**Expected Output:**
```
Starting Real-Time IDS API server on 0.0.0.0:5000
Model: models/ml_best.pkl (ml)
Interface: auto-detect

Endpoints:
  - http://0.0.0.0:5000/
  - http://0.0.0.0:5000/health
  - http://0.0.0.0:5000/predict (POST)
  - http://0.0.0.0:5000/stats
  - http://0.0.0.0:5000/attacks

WebSocket:
  - ws://0.0.0.0:5000/socket.io/

Press Ctrl+C to stop
```

### Option 2: Start Frontend (Terminal 2)
```bash
cd web
npm run dev
```

**Expected Output:**
```
  VITE v4.5.0  ready in XXX ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
```

## 📋 Step-by-Step

### 1. Install Dependencies (if not done)
```bash
# Backend
cd network-anomaly-detection
pip install -r requirements.txt

# Frontend
cd ../web
npm install
```

### 2. Start Backend Server
Open **Terminal 1**:
```bash
cd network-anomaly-detection
python start_realtime_ids.py
```

Wait for: `Starting Real-Time IDS API server...`

### 3. Start Frontend
Open **Terminal 2** (new terminal):
```bash
cd web
npm run dev
```

### 4. Access Dashboard
1. Open browser: `http://localhost:5173`
2. Scroll to "Real-Time Intrusion Detection" section
3. Click "Start Monitoring" button
4. Watch live network traffic analysis!

## 🔧 Troubleshooting

### Backend won't start

**Error: "Module not found"**
```bash
pip install -r network-anomaly-detection/requirements.txt
```

**Error: "Scapy not available"**
```bash
pip install scapy
# Windows: Install Npcap from https://npcap.com/
```

**Error: "Permission denied" (Linux)**
```bash
sudo python start_realtime_ids.py
```

**Error: "Model not found"**
- Ensure model file exists at `models/ml_best.pkl`
- Or specify custom path: `python start_realtime_ids.py --model path/to/model.pkl`

### Frontend won't connect

**Error: "Connection refused"**
- Check backend is running on port 5000
- Verify in browser: `http://localhost:5000/health`

**Error: "Socket.IO connection failed"**
- Check `VITE_API_URL` in `web/.env` (should be `http://localhost:5000`)
- Restart frontend after changing `.env`

### No packets captured

**Check network interface:**
```python
python -c "from scapy.all import get_if_list; print(get_if_list())"
```

**Specify interface:**
```bash
python start_realtime_ids.py --interface "Wi-Fi"
# or
python start_realtime_ids.py --interface "Ethernet"
```

## ✅ Verification

### Check Backend
```bash
# Health check
curl http://localhost:5000/health

# Or in browser
http://localhost:5000/health
```

### Check Frontend
- Open: `http://localhost:5173`
- Look for "Real-Time Intrusion Detection" section
- Connection status should show "Connected"

## 🎯 What to Expect

1. **Backend starts** → Shows server info and endpoints
2. **Frontend loads** → React app with Real-Time Dashboard section
3. **Click "Start Monitoring"** → Status changes to "Monitoring Active"
4. **See live updates** → Predictions stream in real-time
5. **Attacks detected** → Red alerts appear in dashboard

## 📊 Monitoring

- **Backend logs**: Check terminal where backend is running
- **Attack logs**: `network-anomaly-detection/logs/attacks.log`
- **Frontend console**: Browser DevTools (F12) → Console tab

## 🛑 Stopping

- **Backend**: Press `Ctrl+C` in Terminal 1
- **Frontend**: Press `Ctrl+C` in Terminal 2

---

**Need help?** Check `REALTIME_IDS.md` for full documentation.


