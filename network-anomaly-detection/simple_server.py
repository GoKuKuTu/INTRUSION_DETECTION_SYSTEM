#!/usr/bin/env python3
"""
Simple test server for the Network Anomaly Detection frontend
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import uvicorn

app = FastAPI(title="Network Anomaly Detection API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)

class FeatureRequest(BaseModel):
    features: List[float]

@app.get("/")
async def root():
    return {"message": "Network Anomaly Detection API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

@app.post("/predict")
async def predict(request: FeatureRequest):
    """Simple prediction endpoint for testing with specific anomaly types"""
    try:
        # Simple mock prediction based on feature values
        features = request.features
        
        if not features or len(features) < 5:
            return {"error": "At least 5 features required"}
        
        # Extract features (assuming: flow_duration, packet_count, byte_count, protocol, port)
        flow_duration, packet_count, byte_count, protocol, port = features[:5]
        
        # Determine anomaly type based on feature patterns
        anomaly_type = "normal"
        confidence = 0.0
        
        # DDoS Attack - High packet count and byte count
        if packet_count > 1000 and byte_count > 50000:
            anomaly_type = "DDoS Attack"
            confidence = min((packet_count + byte_count/100) / 2000, 1.0)
        
        # Port Scan - High flow duration with low packet count
        elif flow_duration > 500 and packet_count < 10:
            anomaly_type = "Port Scan"
            confidence = min(flow_duration / 1000, 1.0)
        
        # Brute Force - High packet count with low byte count
        elif packet_count > 500 and byte_count < 1000:
            anomaly_type = "Brute Force Attack"
            confidence = min(packet_count / 1000, 1.0)
        
        # Suspicious Protocol - Unusual protocol usage
        elif protocol not in [1, 6, 17]:  # Not ICMP, TCP, or UDP
            anomaly_type = "Suspicious Protocol"
            confidence = 0.8
        
        # Suspicious Port - Well-known attack ports
        elif port in [22, 23, 135, 139, 445, 1433, 3389]:  # SSH, Telnet, RPC, SMB, SQL, RDP
            anomaly_type = "Suspicious Port Access"
            confidence = 0.7
        
        # High Traffic - Very high byte count
        elif byte_count > 100000:
            anomaly_type = "High Traffic Anomaly"
            confidence = min(byte_count / 200000, 1.0)
        
        # Long Duration - Suspiciously long flow
        elif flow_duration > 1000:
            anomaly_type = "Long Duration Flow"
            confidence = min(flow_duration / 2000, 1.0)
        
        # Normal traffic
        else:
            anomaly_type = "normal"
            confidence = 0.1  # Low confidence for normal traffic
        
        return {
            "label": "anomaly" if anomaly_type != "normal" else "normal",
            "anomaly_type": anomaly_type,
            "score": confidence,
            "model": "enhanced_test_model",
            "model_type": "ml",
            "details": {
                "flow_duration": flow_duration,
                "packet_count": packet_count,
                "byte_count": byte_count,
                "protocol": protocol,
                "port": port
            }
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    print("Starting simple test server...")
    print("API will be available at: http://localhost:8000")
    print("Health check: http://localhost:8000/health")
    print("API docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
