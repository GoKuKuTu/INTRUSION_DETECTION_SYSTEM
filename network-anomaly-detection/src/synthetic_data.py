#!/usr/bin/env python3
"""
Synthetic Network Flow Data Generator

This script generates synthetic network flow data for testing and development
purposes. It creates realistic network traffic features that can be used for
anomaly detection model development and testing.

Features generated include:
- Flow duration, packet counts, byte counts
- Protocol information, port numbers
- Timing statistics (inter-arrival times)
- Flag information (TCP flags)
- Anomaly labels (normal vs various attack types)

Usage:
    python src/synthetic_data.py --rows 100 --output data/raw/sample.csv
    python src/synthetic_data.py --rows 1000 --anomaly_ratio 0.1 --output data/raw/test_data.csv
"""

import argparse
import pandas as pd
import numpy as np
import random
from pathlib import Path
from typing import List, Tuple
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NetworkFlowGenerator:
    """
    Generator for synthetic network flow data with realistic characteristics.
    
    This class creates network flow records that mimic real network traffic
    patterns, including both normal traffic and various types of anomalies
    such as DDoS attacks, port scans, and data exfiltration attempts.
    """
    
    def __init__(self, seed: int = 42):
        """
        Initialize the network flow generator.
        
        Args:
            seed (int): Random seed for reproducible data generation
        """
        self.seed = seed
        np.random.seed(seed)
        random.seed(seed)
        
        # Define attack types and their characteristics
        self.attack_types = {
            'BENIGN': {'weight': 0.7, 'duration_range': (1, 1000), 'packet_range': (1, 100)},
            'DDoS': {'weight': 0.1, 'duration_range': (1, 10), 'packet_range': (1000, 10000)},
            'PortScan': {'weight': 0.05, 'duration_range': (1, 100), 'packet_range': (10, 1000)},
            'DataExfiltration': {'weight': 0.05, 'duration_range': (100, 10000), 'packet_range': (100, 1000)},
            'BruteForce': {'weight': 0.05, 'duration_range': (10, 1000), 'packet_range': (50, 500)},
            'Malware': {'weight': 0.05, 'duration_range': (1, 100), 'packet_range': (10, 100)}
        }
        
        # Common ports and protocols
        self.common_ports = [80, 443, 22, 21, 25, 53, 110, 143, 993, 995, 3389, 5900]
        self.protocols = ['TCP', 'UDP', 'ICMP']
        
    def generate_flow_features(self, attack_type: str, num_flows: int) -> pd.DataFrame:
        """
        Generate network flow features for a specific attack type.
        
        Args:
            attack_type (str): Type of attack/traffic to generate
            num_flows (int): Number of flows to generate
            
        Returns:
            pd.DataFrame: Generated flow data
        """
        attack_config = self.attack_types[attack_type]
        
        # Generate basic flow characteristics
        flows = []
        
        for _ in range(num_flows):
            # Flow duration (milliseconds)
            duration = np.random.uniform(*attack_config['duration_range'])
            
            # Packet counts
            fwd_packets = np.random.randint(1, attack_config['packet_range'][1])
            bwd_packets = np.random.randint(0, fwd_packets) if attack_type != 'DDoS' else 0
            
            # Byte counts (packets * average packet size)
            avg_packet_size = np.random.uniform(64, 1500)
            fwd_bytes = int(fwd_packets * avg_packet_size)
            bwd_bytes = int(bwd_packets * avg_packet_size)
            
            # Protocol and port information
            protocol = np.random.choice(self.protocols)
            dst_port = np.random.choice(self.common_ports)
            
            # Timing features
            flow_iat_mean = duration / max(fwd_packets + bwd_packets, 1)
            flow_iat_std = flow_iat_mean * np.random.uniform(0.1, 0.5)
            
            # TCP flags (simplified)
            fin_count = np.random.randint(0, 2)
            syn_count = np.random.randint(0, 3)
            rst_count = np.random.randint(0, 2)
            psh_count = np.random.randint(0, 5)
            ack_count = max(fwd_packets, bwd_packets)
            urg_count = np.random.randint(0, 2)
            
            # Attack-specific modifications
            if attack_type == 'DDoS':
                # High packet rate, short duration
                fwd_packets = np.random.randint(1000, 10000)
                duration = np.random.uniform(1, 10)
                syn_count = fwd_packets  # SYN flood
            elif attack_type == 'PortScan':
                # Many small packets to different ports
                fwd_packets = np.random.randint(10, 1000)
                bwd_packets = 0
                syn_count = fwd_packets
            elif attack_type == 'DataExfiltration':
                # Large data transfers
                fwd_bytes = np.random.randint(100000, 1000000)
                bwd_bytes = 0
                duration = np.random.uniform(1000, 10000)
            
            # Calculate derived features
            flow_bytes_per_sec = (fwd_bytes + bwd_bytes) / max(duration / 1000, 0.001)
            flow_packets_per_sec = (fwd_packets + bwd_packets) / max(duration / 1000, 0.001)
            
            flow = {
                'src_ip': f"192.168.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}",
                'dst_ip': f"10.0.{np.random.randint(1, 255)}.{np.random.randint(1, 255)}",
                'src_port': np.random.randint(1024, 65535),
                'dst_port': dst_port,
                'protocol': protocol,
                'flow_duration': duration,
                'fwd_packets': fwd_packets,
                'bwd_packets': bwd_packets,
                'fwd_bytes': fwd_bytes,
                'bwd_bytes': bwd_bytes,
                'flow_bytes_per_sec': flow_bytes_per_sec,
                'flow_packets_per_sec': flow_packets_per_sec,
                'flow_iat_mean': flow_iat_mean,
                'flow_iat_std': flow_iat_std,
                'fin_count': fin_count,
                'syn_count': syn_count,
                'rst_count': rst_count,
                'psh_count': psh_count,
                'ack_count': ack_count,
                'urg_count': urg_count,
                'packet_length_mean': (fwd_bytes + bwd_bytes) / max(fwd_packets + bwd_packets, 1),
                'packet_length_std': avg_packet_size * 0.2,
                'label': attack_type
            }
            
            flows.append(flow)
        
        return pd.DataFrame(flows)
    
    def generate_dataset(self, total_rows: int, anomaly_ratio: float = 0.2) -> pd.DataFrame:
        """
        Generate a complete dataset with normal and anomalous flows.
        
        Args:
            total_rows (int): Total number of rows to generate
            anomaly_ratio (float): Ratio of anomalous flows (0.0 to 1.0)
            
        Returns:
            pd.DataFrame: Complete dataset with all flow types
        """
        logger.info(f"Generating {total_rows} network flows with {anomaly_ratio:.1%} anomaly ratio")
        
        # Calculate number of flows for each type
        normal_flows = int(total_rows * (1 - anomaly_ratio))
        anomaly_flows = total_rows - normal_flows
        
        # Distribute anomaly flows among attack types (excluding BENIGN)
        attack_types = [k for k in self.attack_types.keys() if k != 'BENIGN']
        attack_weights = [self.attack_types[at]['weight'] for at in attack_types]
        attack_weights = np.array(attack_weights) / sum(attack_weights)
        
        attack_counts = np.random.multinomial(anomaly_flows, attack_weights)
        
        # Generate flows for each type
        all_flows = []
        
        # Generate normal flows
        if normal_flows > 0:
            normal_data = self.generate_flow_features('BENIGN', normal_flows)
            all_flows.append(normal_data)
            logger.info(f"Generated {normal_flows} BENIGN flows")
        
        # Generate attack flows
        for attack_type, count in zip(attack_types, attack_counts):
            if count > 0:
                attack_data = self.generate_flow_features(attack_type, count)
                all_flows.append(attack_data)
                logger.info(f"Generated {count} {attack_type} flows")
        
        # Combine all flows and shuffle
        dataset = pd.concat(all_flows, ignore_index=True)
        dataset = dataset.sample(frac=1, random_state=self.seed).reset_index(drop=True)
        
        logger.info(f"Generated complete dataset: {len(dataset)} flows")
        logger.info(f"Label distribution:\n{dataset['label'].value_counts()}")
        
        return dataset


def main():
    """
    Main function to run the synthetic data generator from command line.
    """
    parser = argparse.ArgumentParser(
        description="Generate synthetic network flow data for anomaly detection testing",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/synthetic_data.py --rows 100 --output data/raw/sample.csv
  python src/synthetic_data.py --rows 1000 --anomaly_ratio 0.1 --output data/raw/test_data.csv
  python src/synthetic_data.py --rows 10000 --seed 123 --output data/raw/large_dataset.csv
        """
    )
    
    parser.add_argument(
        '--rows', 
        type=int, 
        default=100,
        help='Number of rows to generate (default: 100)'
    )
    
    parser.add_argument(
        '--anomaly_ratio', 
        type=float, 
        default=0.2,
        help='Ratio of anomalous flows (0.0 to 1.0, default: 0.2)'
    )
    
    parser.add_argument(
        '--output', 
        type=str, 
        default='data/raw/sample.csv',
        help='Output file path (default: data/raw/sample.csv)'
    )
    
    parser.add_argument(
        '--seed', 
        type=int, 
        default=42,
        help='Random seed for reproducible generation (default: 42)'
    )
    
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate arguments
    if args.rows <= 0:
        logger.error("Number of rows must be positive")
        return 1
    
    if not 0 <= args.anomaly_ratio <= 1:
        logger.error("Anomaly ratio must be between 0.0 and 1.0")
        return 1
    
    # Create output directory if it doesn't exist
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        # Generate synthetic data
        generator = NetworkFlowGenerator(seed=args.seed)
        dataset = generator.generate_dataset(args.rows, args.anomaly_ratio)
        
        # Save to CSV
        dataset.to_csv(output_path, index=False)
        logger.info(f"Successfully saved {len(dataset)} flows to {output_path}")
        
        # Print summary statistics
        print(f"\nDataset Summary:")
        print(f"Total flows: {len(dataset)}")
        print(f"Features: {len(dataset.columns)}")
        print(f"Anomaly ratio: {args.anomaly_ratio:.1%}")
        print(f"Label distribution:")
        for label, count in dataset['label'].value_counts().items():
            print(f"  {label}: {count} ({count/len(dataset):.1%})")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error generating synthetic data: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
