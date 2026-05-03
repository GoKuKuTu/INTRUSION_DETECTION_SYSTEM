#!/usr/bin/env python3
"""
Test script to verify attack detection and display in terminal.
Run the realtime_ids server first, then run this script in another terminal.
"""

import requests
import time
import sys

BASE_URL = "http://localhost:5001"

# List of test attacks to emit
ATTACKS = [
    {"count": 3, "anomaly_type": "DDoS Attack", "model": "rule-based"},
    {"count": 2, "anomaly_type": "Port Scan", "model": "rule-based"},
    {"count": 2, "anomaly_type": "Brute Force Attack", "model": "rule-based"},
    {"count": 2, "anomaly_type": "Suspicious Protocol", "model": "rule-based"},
]

def test_attacks():
    """Send test attack events to the server."""
    print("=" * 80)
    print("🚀 TESTING ATTACK DETECTION SYSTEM")
    print("=" * 80)
    print("\nSending synthetic attack events to the server...")
    print("Watch the server terminal for attack detections!\n")
    
    for attack_config in ATTACKS:
        count = attack_config["count"]
        attack_type = attack_config["anomaly_type"]
        model = attack_config["model"]
        
        # Build the URL with query parameters
        url = f"{BASE_URL}/emit_test"
        params = {
            "count": count,
            "anomaly_type": attack_type,
            "model": model,
            "label": "anomaly",
            "allow_when_stopped": "true"
        }
        
        try:
            print(f"📤 Emitting {count} × {attack_type}...", end=" ", flush=True)
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ Success")
                result = response.json()
                print(f"   Emitted: {result.get('count')} events")
            else:
                print(f"❌ Failed (Status: {response.status_code})")
                print(f"   Response: {response.text}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        time.sleep(1)
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE - Check the server terminal for attack detections!")
    print("=" * 80)

if __name__ == "__main__":
    try:
        test_attacks()
    except KeyboardInterrupt:
        print("\n\n⏹️  Test interrupted by user")
        sys.exit(0)
