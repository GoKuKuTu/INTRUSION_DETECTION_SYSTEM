# Real-Time Intrusion Detection System

## Overview

This project has been upgraded from a batch-based CSV prediction system to a **real-time Intrusion Detection System (IDS)** that monitors live network traffic and detects anomalies in real-time.

## Architecture

```
┌─────────────────┐
│  Network Traffic│
│   (Live Packets)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Traffic Capture │  ← Scapy captures live packets
│   (Scapy)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Flow Extraction │  ← Groups packets into flows
│   (5-tuple)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│Feature Extraction│ ← Extracts CICFlowMeter-compatible features
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  ML/DL Model    │  ← Pre-loaded model makes predictions
│  (Prediction)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Flask API      │  ← REST + WebSocket endpoints
│  (Socket.IO)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ React Frontend  │  ← Real-time dashboard updates
│  (Socket.IO)    │
└─────────────────┘
```

## Features

1. **Live Network Traffic Capture**: Uses Scapy to capture packets from network interface
2. **Flow-Based Feature Extraction**: Extracts CICFlowMeter-compatible features from network flows
3. **Real-Time Prediction**: Pre-loaded ML/DL models make predictions on streaming data
4. **WebSocket Streaming**: Socket.IO streams predictions to frontend in real-time
5. **Attack Logging**: All detected attacks are logged with timestamp, IPs, and attack type
6. **Alert System**: Visual alerts in the dashboard when attacks are detected
7. **Low Latency**: Optimized for real-time performance

## Installation

### 1. Install Python Dependencies

```bash
cd network-anomaly-detection
pip install -r requirements.txt
```

**Note**: On Windows, you may need to install Npcap (WinPcap replacement) for Scapy:
- Download from: https://npcap.com/

On Linux/Mac:
```bash
# May need to install libpcap
sudo apt-get install libpcap-dev  # Ubuntu/Debian
brew install libpcap              # macOS
```

### 2. Install Frontend Dependencies

```bash
cd web
npm install
```

## Usage

### Starting the Real-Time IDS Backend

```bash
cd network-anomaly-detection

# Basic usage (auto-detects interface, uses default model)
python start_realtime_ids.py

# With custom model
python start_realtime_ids.py --model models/ml_best.pkl --model-type ml

# With specific network interface
python start_realtime_ids.py --interface eth0

# Custom port
python start_realtime_ids.py --port 5000
```

**Command-line Options:**
- `--model`: Path to model file (default: `models/ml_best.pkl`)
- `--model-type`: Type of model - `ml` or `dl` (default: `ml`)
- `--interface`: Network interface name (default: auto-detect)
- `--port`: Port to run server on (default: 5000)
- `--host`: Host to bind to (default: 0.0.0.0)

### Starting the Frontend

```bash
cd web
npm run dev
```

The frontend will be available at `http://localhost:5173`

### Configuration

Set environment variable for API URL (if different from default):
```bash
# In web/.env
VITE_API_URL=http://localhost:5000
```

## API Endpoints

### REST Endpoints

- `GET /` - API information
- `GET /health` - Health check
- `POST /predict` - Real-time prediction endpoint
  ```json
  {
    "features": {
      "src_ip": 1.0,
      "dst_ip": -1.0,
      "src_port": 0.5,
      "dst_port": -0.5,
      "flow_duration": 100.0,
      ...
    }
  }
  ```
- `GET /stats` - System statistics
- `GET /attacks` - Recent attack logs

### WebSocket Events

**Client → Server:**
- `start_monitoring` - Start real-time monitoring
- `stop_monitoring` - Stop real-time monitoring

**Server → Client:**
- `prediction` - New prediction result
- `status` - Status updates
- `connected` - Connection confirmation

## Project Structure

```
network-anomaly-detection/
├── src/
│   ├── traffic_capture.py      # Live packet capture with Scapy
│   ├── feature_extractor.py    # Flow-based feature extraction
│   ├── realtime_predictor.py   # Real-time prediction service
│   ├── realtime_api.py         # Flask API with WebSocket
│   ├── api.py                  # Original FastAPI (still available)
│   └── preprocess.py           # Data preprocessing
├── logs/
│   └── attacks.log             # Attack logs (auto-created)
├── models/                     # ML/DL model files
├── start_realtime_ids.py       # Startup script
└── REALTIME_IDS.md            # This file

web/
├── src/
│   ├── components/
│   │   ├── RealtimeDashboard.jsx  # Real-time monitoring dashboard
│   │   └── ...
│   └── App.jsx
└── package.json
```

## How It Works

### 1. Traffic Capture
- Scapy captures live packets from the network interface
- Packets are grouped into flows using 5-tuple (src_ip, dst_ip, src_port, dst_port, protocol)
- Flows expire after 30 seconds of inactivity

### 2. Feature Extraction
- For each completed flow, features are extracted matching the training data format
- Features include: flow duration, packet counts, byte counts, inter-arrival times, TCP flags, etc.
- Features are normalized to match the preprocessing pipeline

### 3. Real-Time Prediction
- Pre-loaded ML/DL model makes predictions on extracted features
- Predictions include: label (normal/anomaly), confidence score, attack type
- Low-latency processing for real-time performance

### 4. WebSocket Streaming
- Predictions are streamed to connected clients via Socket.IO
- Frontend receives updates in real-time without polling

### 5. Attack Logging
- All detected attacks are logged to `logs/attacks.log`
- Log format: JSON with timestamp, IPs, ports, attack type, confidence

## Attack Types Detected

- **DDoS Attack**: High packet/byte rate, short duration
- **Port Scan**: Many small packets to different ports
- **Brute Force**: High packet count with low byte count
- **Data Exfiltration**: Large data transfers
- **Malware**: Suspicious traffic patterns
- **Suspicious Protocol**: Unusual protocol usage
- **Suspicious Port**: Access to well-known attack ports

## Performance Considerations

1. **Model Loading**: Models are loaded once at startup for efficiency
2. **Flow Timeout**: Flows expire after 30 seconds to prevent memory buildup
3. **Batch Processing**: Multiple flows can be processed efficiently
4. **WebSocket**: Low-latency streaming without HTTP overhead

## Troubleshooting

### Scapy Permission Issues (Linux)

```bash
# Run with sudo or set capabilities
sudo python start_realtime_ids.py

# Or set capabilities
sudo setcap cap_net_raw,cap_net_admin=eip /usr/bin/python3
```

### No Packets Captured

- Check network interface name: `python -c "from scapy.all import get_if_list; print(get_if_list())"`
- Ensure interface is active and has traffic
- On Windows, ensure Npcap is installed

### Model Not Found

- Ensure model file exists at specified path
- Check that preprocessing components (scaler, encoders) are in the same directory

### Frontend Connection Issues

- Check API URL in `.env` file
- Ensure backend is running on correct port
- Check CORS settings if accessing from different origin

## Security Notes

⚠️ **Important**: This system requires network interface access which may require elevated privileges. Use responsibly and only on networks you own or have permission to monitor.

- The system captures live network traffic
- Ensure compliance with local network policies
- Attack logs may contain sensitive information
- Use HTTPS/WSS in production environments

## Future Enhancements

- [ ] Support for multiple models (ensemble)
- [ ] Historical data visualization
- [ ] Automated response actions
- [ ] Machine learning model retraining pipeline
- [ ] Distributed monitoring across multiple interfaces
- [ ] Integration with SIEM systems

## License

Same as the main project.

## Support

For issues or questions, refer to the main project documentation or create an issue in the repository.

