#!/usr/bin/env python3
"""
Real-Time Feature Extraction Module

This module extracts flow-based features from network traffic flows
that are compatible with the trained ML models.

Features extracted match the CICFlowMeter format and are compatible
with the preprocessing pipeline used during training.
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Optional

# Import Flow class - handle both direct import and relative import
try:
    from traffic_capture import Flow
except ImportError:
    from .traffic_capture import Flow

logger = logging.getLogger(__name__)


class FeatureExtractor:
    """
    Extracts features from network flows for ML model prediction.
    """
    
    def __init__(self):
        """Initialize feature extractor."""
        self.protocol_map = {'TCP': 6, 'UDP': 17, 'ICMP': 1, 'UNKNOWN': 0}
        logger.info("FeatureExtractor initialized")
    
    def extract_features(self, flow: Flow) -> Dict[str, float]:
        """
        Extract features from a flow compatible with trained models.
        
        Args:
            flow: Flow object with packet information
            
        Returns:
            Dictionary of feature names and values
        """
        try:
            # Basic flow information
            flow_duration = flow.get_duration()
            total_packets = flow.fwd_packets + flow.bwd_packets
            total_bytes = flow.fwd_bytes + flow.bwd_bytes
            
            # Protocol encoding (numeric)
            protocol_num = self.protocol_map.get(flow.protocol, 0)
            
            # Build simplified feature dictionary with only 5 features
            features = {
                'flow_duration': flow_duration,
                'packet_count': float(total_packets),
                'byte_count': float(total_bytes),
                'protocol': float(protocol_num),
                'port': float(flow.dst_port),  # Use destination port
            }
            
            return features
            
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            raise
    
    def _ip_to_numeric(self, ip: str) -> float:
        """
        Convert IP address to numeric representation.
        Uses a simple hash-based approach for consistency.
        """
        try:
            parts = ip.split('.')
            if len(parts) == 4:
                # Convert to integer and normalize
                ip_int = sum(int(parts[i]) * (256 ** (3-i)) for i in range(4))
                # Normalize to similar range as training data
                return (ip_int - 2147483648) / 2147483648.0
            else:
                # IPv6 or invalid - use hash
                return hash(ip) % 1000000 / 1000000.0
        except:
            return 0.0
    
    def _normalize_psh_count(self, psh_count: int) -> List[float]:
        """
        Normalize PSH count to match training data encoding.
        Returns list of normalized values for psh_count_0 through psh_count_4.
        """
        # Based on training data patterns
        if psh_count == 0:
            return [1.5646967316604727, -0.5465357250000211, -0.5310850045437943, -0.3692744729379982, -0.3692744729379982]
        elif psh_count == 1:
            return [-0.6391014819458268, 1.8297065576087663, -0.5310850045437943, -0.3692744729379982, -0.3692744729379982]
        elif psh_count == 2:
            return [-0.6391014819458268, -0.5465357250000211, 1.8827149944562057, -0.3692744729379982, -0.3692744729379982]
        elif psh_count == 3:
            return [-0.6391014819458268, -0.5465357250000211, -0.5310850045437943, 2.7080128015453204, -0.3692744729379982]
        elif psh_count >= 4:
            return [-0.6391014819458268, -0.5465357250000211, -0.5310850045437943, -0.3692744729379982, 2.7080128015453204]
        else:
            return [-0.6391014819458268, -0.5465357250000211, -0.5310850045437943, -0.3692744729379982, -0.3692744729379982]
    
    def features_to_array(self, features: Dict[str, float], feature_order: Optional[List[str]] = None) -> np.ndarray:
        """
        Convert feature dictionary to numpy array.
        
        Args:
            features: Feature dictionary
            feature_order: Optional list of feature names in order (if None, uses dict order)
            
        Returns:
            Numpy array of feature values
        """
        if feature_order:
            return np.array([features.get(name, 0.0) for name in feature_order], dtype=float)
        else:
            return np.array(list(features.values()), dtype=float)
    
    def extract_features_batch(self, flows: List[Flow]) -> pd.DataFrame:
        """
        Extract features from multiple flows.
        
        Args:
            flows: List of Flow objects
            
        Returns:
            DataFrame with extracted features
        """
        feature_list = []
        for flow in flows:
            try:
                features = self.extract_features(flow)
                feature_list.append(features)
            except Exception as e:
                logger.error(f"Error extracting features from flow: {e}")
                continue
        
        if not feature_list:
            return pd.DataFrame()
        
        return pd.DataFrame(feature_list)

