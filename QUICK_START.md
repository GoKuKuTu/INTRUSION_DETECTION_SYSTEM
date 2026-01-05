# Quick Start Guide - Real-Time IDS

## 🚀 Quick Setup (5 minutes)

### 1. Install Backend Dependencies
```bash
cd network-anomaly-detection
pip install -r requirements.txt
```

**Note for Windows**: Install Npcap from https://npcap.com/ for Scapy to work.

**Note for Linux**: May need `sudo apt-get install libpcap-dev` or run with `sudo`.

### 2. Install Frontend Dependencies
```bash
cd web
npm install
```

### 3. Start Backend Server
```bash
# From network-anomaly-detection directory
python start_realtime_ids.py
```

The server will start on `http://localhost:5000`

### 4. Start Frontend
```bash
# From web directory
npm run dev
```

The frontend will be available at `http://localhost:5173`

### 5. Use Real-Time Dashboard
1. Open `http://localhost:5173` in your browser
2. Scroll to "Real-Time Intrusion Detection" section
3. Click "Start Monitoring" button
4. Watch live network traffic analysis!

## 📋 What Was Implemented

✅ **Live Network Traffic Capture** - Scapy captures packets in real-time  
✅ **Flow-Based Feature Extraction** - CICFlowMeter-compatible features  
✅ **Real-Time ML Predictions** - Pre-loaded models make instant predictions  
✅ **WebSocket Streaming** - Socket.IO streams predictions to frontend  
✅ **Live Dashboard** - React component with real-time updates  
✅ **Attack Alerts** - Visual alerts when intrusions detected  
✅ **Attack Logging** - All attacks logged with full details  

## 📁 New Files Created

### Backend
- `src/traffic_capture.py` - Live packet capture
- `src/feature_extractor.py` - Feature extraction
- `src/realtime_predictor.py` - Real-time prediction service
- `src/realtime_api.py` - Flask API with WebSocket
- `start_realtime_ids.py` - Startup script

### Frontend
- `src/components/RealtimeDashboard.jsx` - Real-time dashboard component

### Documentation
- `REALTIME_IDS.md` - Full documentation
- `REALTIME_IDS_IMPLEMENTATION.md` - Implementation details
- `QUICK_START.md` - This file

### Scripts
- `start_realtime_ids.bat` - Windows startup
- `start_realtime_ids.sh` - Linux/Mac startup

## 🎯 Key Features

1. **Real-Time Processing**: No CSV files - live network monitoring
2. **Low Latency**: Optimized for sub-second predictions
3. **WebSocket Streaming**: Real-time updates without polling
4. **Attack Detection**: Identifies DDoS, Port Scans, Brute Force, etc.
5. **Visual Dashboard**: Beautiful React UI with live statistics
6. **Attack Logging**: JSON logs with timestamp, IPs, attack type

## 🔧 Configuration

### Backend Port
Default: `5000`
```bash
python start_realtime_ids.py --port 8080
```

### Network Interface
Auto-detects by default, or specify:
```bash
python start_realtime_ids.py --interface eth0
```

### Model Selection
```bash
python start_realtime_ids.py --model models/ml_best.pkl --model-type ml
```

### Frontend API URL
Create `web/.env`:
```
VITE_API_URL=http://localhost:5000
```

## 📊 API Endpoints

- `GET /health` - Health check
- `POST /predict` - Real-time prediction
- `GET /stats` - System statistics
- `GET /attacks` - Recent attack logs

## 🔌 WebSocket Events

**Client → Server:**
- `start_monitoring` - Start monitoring
- `stop_monitoring` - Stop monitoring

**Server → Client:**
- `prediction` - New prediction result
- `status` - Status updates

## 🐛 Troubleshooting

### "Scapy not available"
```bash
pip install scapy
```

### "Permission denied" (Linux)
```bash
sudo python start_realtime_ids.py
# Or set capabilities:
sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/python3
```

### "No packets captured"
- Check network interface: `python -c "from scapy.all import get_if_list; print(get_if_list())"`
- Ensure interface is active
- On Windows: Install Npcap

### Frontend not connecting
- Check backend is running on correct port
- Verify `VITE_API_URL` in `web/.env`
- Check browser console for errors

## 📚 Full Documentation

See `network-anomaly-detection/REALTIME_IDS.md` for complete documentation.

## 🎓 Interview/Viva Ready

This implementation is production-ready and interview-ready:
- ✅ Clean, modular code structure
- ✅ Comprehensive documentation
- ✅ Real-time performance optimized
- ✅ Error handling and logging
- ✅ Scalable architecture
- ✅ Security considerations

## 🎉 You're Ready!

Your real-time IDS is now fully functional. Start monitoring your network traffic in real-time!

