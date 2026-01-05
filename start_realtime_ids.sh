#!/bin/bash
# Startup script for Real-Time IDS (Linux/Mac)

echo "Starting Real-Time Intrusion Detection System..."
echo

cd network-anomaly-detection

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python3 is not installed"
    exit 1
fi

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Check if running as root (needed for packet capture on Linux)
if [ "$EUID" -ne 0 ] && [ "$(uname)" == "Linux" ]; then
    echo "WARNING: May need sudo privileges for packet capture on Linux"
    echo "If you encounter permission errors, run with: sudo $0"
    echo
fi

# Start the real-time IDS
echo "Starting Real-Time IDS API server..."
python3 start_realtime_ids.py "$@"

