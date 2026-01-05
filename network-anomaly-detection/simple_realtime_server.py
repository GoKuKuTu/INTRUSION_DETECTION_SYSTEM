#!/usr/bin/env python3
"""
Simplified Real-Time IDS Server - Works without full IDS initialization
"""
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Setup Socket.IO
try:
    import eventlet
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', logger=True, engineio_logger=True)
except ImportError:
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=True)

# Routes
@app.route('/')
def root():
    return jsonify({
        'message': 'Real-Time IDS API (Simplified)',
        'version': '2.0.0',
        'status': 'running'
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'message': 'API is running',
        'ids_running': False,
        'model_loaded': False
    })

@app.route('/stats')
def stats():
    return jsonify({
        'active_flows': 0,
        'ids_running': False,
        'model_type': 'none',
        'model_path': 'none'
    })

# Socket.IO Events
@socketio.on('connect')
def handle_connect():
    logger.info(f"Client connected")
    print(f"[Socket.IO] ✅ Client connected")
    emit('connected', {'message': 'Connected to Real-Time IDS', 'status': 'connected'})

@socketio.on('disconnect')
def handle_disconnect():
    logger.info(f"Client disconnected")
    print(f"[Socket.IO] ❌ Client disconnected")

@socketio.on('start_monitoring')
def handle_start_monitoring():
    logger.info("Start monitoring requested")
    emit('status', {'message': 'Monitoring started (simplified mode)'})

@socketio.on('stop_monitoring')
def handle_stop_monitoring():
    logger.info("Stop monitoring requested")
    emit('status', {'message': 'Monitoring stopped'})

if __name__ == '__main__':
    print("=" * 50)
    print("  Real-Time IDS Server (Simplified)")
    print("=" * 50)
    print("\nStarting server on http://0.0.0.0:5000")
    print("Health check: http://localhost:5000/health")
    print("Socket.IO: ws://localhost:5000/socket.io/")
    print("\nPress Ctrl+C to stop\n")
    
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\nServer stopped")

