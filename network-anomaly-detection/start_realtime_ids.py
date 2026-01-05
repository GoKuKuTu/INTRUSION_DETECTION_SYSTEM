#!/usr/bin/env python3
"""
Startup script for Real-Time Intrusion Detection System

This script starts the real-time IDS API server with proper configuration.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from realtime_api import main

if __name__ == '__main__':
    sys.exit(main())

