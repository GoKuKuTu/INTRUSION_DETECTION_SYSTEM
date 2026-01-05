#!/usr/bin/env python3
"""Simple test server to debug connection issues"""
import sys
from pathlib import Path

print("Testing minimal Flask + Socket.IO server...")

try:
    from flask import Flask
    from flask_cors import CORS
    from flask_socketio import SocketIO, emit
    print("✅ Flask imports OK")
except ImportError as e:
    print(f"❌ Flask import error: {e}")
    sys.exit(1)

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

try:
    import eventlet
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', logger=True)
    print("✅ Socket.IO with eventlet OK")
except ImportError:
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True)
    print("✅ Socket.IO with threading OK")

@app.route('/health')
def health():
    return {"status": "healthy", "message": "Test server running"}

@socketio.on('connect')
def handle_connect():
    print(f"Client connected: {socketio.server.session_manager}")
    emit('connected', {'message': 'Connected to test server'})

@socketio.on('disconnect')
def handle_disconnect():
    print("Client disconnected")

if __name__ == '__main__':
    print("\n🚀 Starting test server on http://localhost:5000")
    print("   Test: http://localhost:5000/health")
    print("   Press Ctrl+C to stop\n")
    try:
        socketio.run(app, host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        print("\nServer stopped")

