#!/usr/bin/env python3
"""
Test script for Adaptive Real-Time Predictor

Tests the complexity-based model selection functionality.
"""

import sys
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from adaptive_predictor import AdaptiveRealtimePredictor
from feature_extractor import FeatureExtractor

def ip_to_numeric(ip: str) -> float:
    """Convert IP address to numeric representation (same as FeatureExtractor)."""
    try:
        parts = ip.split('.')
        if len(parts) == 4:
            ip_int = sum(int(parts[i]) * (256 ** (3-i)) for i in range(4))
            return (ip_int - 2147483648) / 2147483648.0
        else:
            return hash(ip) % 1000000 / 1000000.0
    except:
        return 0.0

def test_adaptive_predictor():
    """Test the adaptive predictor with different complexity levels."""

    # Initialize predictor
    predictor = AdaptiveRealtimePredictor(
        ml_model_path='models/ml_best.pkl',
        dl_model_path='models/dl_lstm.h5',
        complexity_threshold=50.0
    )

    print("🧠 Testing Adaptive Real-Time Predictor")
    print("=" * 50)

    # Test cases with different complexity levels
    test_cases = [
        {
            'name': 'Simple HTTP Request',
            'features': {
                'src_ip': ip_to_numeric('192.168.1.100'),
                'dst_ip': ip_to_numeric('10.0.0.1'),
                'src_port': (54321 - 32768) / 32768.0,  # Normalized
                'dst_port': (80 - 32768) / 32768.0,
                'flow_duration': 0.5,
                'fwd_packets': 3.0,
                'bwd_packets': 2.0,
                'fwd_bytes': 200.0,
                'bwd_bytes': 1500.0,
                'flow_bytes_per_sec': 3400.0,
                'flow_packets_per_sec': 10.0,
                'flow_iat_mean': 0.1,
                'flow_iat_std': 0.05,
                'syn_count': 1.0,
                'ack_count': 2.0,
                'packet_length_mean': 400.0,
                'packet_length_std': 200.0,
                'protocol_ICMP': 0,
                'protocol_TCP': 1,
                'protocol_UDP': 0,
                'fin_count_0': 0,
                'fin_count_1': 1,
                'rst_count_0': 0,
                'rst_count_1': 0,
                'psh_count_0': 1,
                'psh_count_1': 0,
                'psh_count_2': 0,
                'psh_count_3': 0,
                'psh_count_4': 0,
                'urg_count_0': 0,
                'urg_count_1': 0
            }
        },
        {
            'name': 'Complex Data Transfer',
            'features': {
                'src_ip': ip_to_numeric('192.168.1.100'),
                'dst_ip': ip_to_numeric('10.0.0.1'),
                'src_port': (54321 - 32768) / 32768.0,
                'dst_port': (443 - 32768) / 32768.0,
                'flow_duration': 120.0,  # Long duration
                'fwd_packets': 500.0,      # Many packets
                'bwd_packets': 800.0,
                'fwd_bytes': 50000.0,      # Large data
                'bwd_bytes': 200000.0,
                'flow_bytes_per_sec': 208333.0,
                'flow_packets_per_sec': 1083.0,
                'flow_iat_mean': 0.05,
                'flow_iat_std': 0.2,     # High variance
                'syn_count': 1.0,
                'ack_count': 100.0,
                'packet_length_mean': 800.0,
                'packet_length_std': 400.0,  # High variance
                'protocol_ICMP': 0,
                'protocol_TCP': 1,
                'protocol_UDP': 0,
                'fin_count_0': 0,
                'fin_count_1': 1,
                'rst_count_0': 0,
                'rst_count_1': 0,
                'psh_count_0': 50,
                'psh_count_1': 0,
                'psh_count_2': 0,
                'psh_count_3': 0,
                'psh_count_4': 0,
                'urg_count_0': 0,
                'urg_count_1': 0
            }
        },
        {
            'name': 'DDoS Attack Pattern',
            'features': {
                'src_ip': ip_to_numeric('192.168.1.100'),
                'dst_ip': ip_to_numeric('10.0.0.1'),
                'src_port': (54321 - 32768) / 32768.0,
                'dst_port': (80 - 32768) / 32768.0,
                'flow_duration': 300.0,  # Very long
                'fwd_packets': 2000.0,     # Many packets
                'bwd_packets': 50.0,
                'fwd_bytes': 120000.0,    # Large data
                'bwd_bytes': 3000.0,
                'flow_bytes_per_sec': 410.0,
                'flow_packets_per_sec': 6.8,
                'flow_iat_mean': 0.01,
                'flow_iat_std': 0.005,
                'syn_count': 2000.0,      # Many SYN packets
                'ack_count': 50.0,
                'packet_length_mean': 60.0,
                'packet_length_std': 10.0,
                'protocol_ICMP': 0,
                'protocol_TCP': 1,
                'protocol_UDP': 0,
                'fin_count_0': 0,
                'fin_count_1': 0,
                'rst_count_0': 0,
                'rst_count_1': 0,
                'psh_count_0': 0,
                'psh_count_1': 0,
                'psh_count_2': 0,
                'psh_count_3': 0,
                'psh_count_4': 0,
                'urg_count_0': 0,
                'urg_count_1': 0
            }
        }
    ]

    print(f"Complexity Threshold: {predictor.complexity_threshold}")
    print(f"ML Model Loaded: {predictor.ml_predictor is not None}")
    print(f"DL Model Loaded: {predictor.dl_predictor is not None}")
    print()

    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}: {test_case['name']}")
        print("-" * 40)

        # Calculate complexity
        complexity = predictor.calculate_complexity(test_case['features'])
        selected_model = predictor.select_model(complexity)

        print(f"Complexity Score: {complexity:.2f}")
        print(f"Selected Model: {selected_model.upper()}")

        # Make prediction
        try:
            prediction = predictor.predict(test_case['features'])
            print(f"Prediction: {prediction['label']} (confidence: {prediction['score']:.4f})")
            print(f"Model Used: {prediction['model_type']}")
            if 'anomaly_type' in prediction:
                print(f"Anomaly Type: {prediction['anomaly_type']}")
        except Exception as e:
            print(f"Prediction failed: {e}")

        print()

    print("✅ Adaptive predictor test completed!")

if __name__ == '__main__':
    test_adaptive_predictor()