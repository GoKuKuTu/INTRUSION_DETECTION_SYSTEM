#!/usr/bin/env python3
"""
Enhanced server startup script for Network Anomaly Detection
"""

import subprocess
import sys
import time
import requests
from pathlib import Path

def install_requirements():
    """Install required packages"""
    print("Installing required packages...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", 
                              "fastapi", "uvicorn", "pandas", "numpy", "scikit-learn", "joblib"])
        print("✅ Packages installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install packages: {e}")
        return False

def check_port_available(port=8000):
    """Check if port is available"""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', port))
            return True
    except OSError:
        return False

def test_api():
    """Test if API is responding"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API is responding correctly!")
            return True
    except requests.exceptions.RequestException:
        pass
    print("❌ API is not responding")
    return False

def main():
    print("🚀 Network Anomaly Detection - Backend Server Setup")
    print("=" * 50)
    
    # Check if port is available
    if not check_port_available():
        print("⚠️  Port 8000 is already in use. Trying to use the existing server...")
        if test_api():
            print("✅ Server is already running and working!")
            return
        else:
            print("❌ Port 8000 is in use but server is not responding properly.")
            print("Please stop any existing servers and try again.")
            return
    
    # Install requirements
    if not install_requirements():
        return
    
    # Start the server
    print("\n🔄 Starting the backend server...")
    print("Server will be available at: http://localhost:8000")
    print("Health check: http://localhost:8000/health")
    print("API docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        # Change to the correct directory
        server_path = Path(__file__).parent / "simple_server.py"
        subprocess.run([sys.executable, str(server_path)])
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

if __name__ == "__main__":
    main()
