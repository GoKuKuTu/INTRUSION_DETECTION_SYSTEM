#!/usr/bin/env python3
"""
Adaptive Real-Time Prediction Service

This module loads both ML and DL models and selects the appropriate model
based on a complexity factor for optimal performance.

Features:
- Dual model loading (ML + DL)
- Complexity-based model selection
- Real-time prediction on flows
- Attack type classification
- Low-latency processing
"""

import logging
import joblib
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import time

# Lazy import for TensorFlow to avoid startup issues
DL_AVAILABLE = False
def _check_tensorflow():
    global DL_AVAILABLE
    if DL_AVAILABLE:
        return True
    try:
        import tensorflow as tf
        from tensorflow import keras
        DL_AVAILABLE = True
        return True
    except Exception as e:
        DL_AVAILABLE = False
        logging.debug(f"TensorFlow not available: {e}")
        return False

# Import FeatureExtractor - handle both direct import and relative import
try:
    from feature_extractor import FeatureExtractor
except ImportError:
    from .feature_extractor import FeatureExtractor

logger = logging.getLogger(__name__)


class AdaptiveRealtimePredictor:
    """
    Adaptive real-time prediction service that selects between rule-based detection,
    ML models for known attacks, and DL models for unknown/novel patterns.

    Strategy:
    - Known attack patterns (DDoS, PortScan, BruteForce, etc.) → Rule-based + ML
    - Unknown/novel patterns → DL models for anomaly detection
    - Normal traffic → ML models for classification
    """

    def __init__(self, ml_model_path: str = None, dl_model_path: str = None, complexity_threshold: float = 50.0):
        """
        Initialize adaptive predictor with rule-based detection for known attacks.

        Args:
            ml_model_path: Path to ML model file (used for known attacks and normal traffic)
            dl_model_path: Path to DL model file (used for unknown/novel patterns)
            complexity_threshold: Threshold for model selection (kept for backward compatibility)
        """
        self.ml_model_path = Path(ml_model_path) if ml_model_path else None
        self.dl_model_path = Path(dl_model_path) if dl_model_path else None
        self.complexity_threshold = complexity_threshold

        # Model instances (optional for rule-based)
        self.ml_predictor = None
        self.dl_predictor = None

        # Shared components (optional for rule-based)
        self.scaler = None
        self.label_encoder = None
        self.feature_names = None
        self.feature_extractor = FeatureExtractor()

        # Attack type mapping
        self.attack_type_map = {
            'BENIGN': 'normal',
            'DDoS': 'DDoS Attack',
            'PortScan': 'Port Scan',
            'DataExfiltration': 'Data Exfiltration',
            'BruteForce': 'Brute Force Attack',
            'Malware': 'Malware',
        }

        logger.info(f"Initializing AdaptiveRealtimePredictor (Rule-based for known attacks, ML/DL for unknown)")
        logger.info(f"Complexity Threshold: {complexity_threshold} (kept for backward compatibility)")

        # Try to load models if provided, but don't fail if not available
        self._load_models()

    def _load_models(self):
        """Load both ML and DL models if available."""
        try:
            # Load ML model if path provided
            if self.ml_model_path and self.ml_model_path.exists():
                logger.info(f"Loading ML model: {self.ml_model_path}")
                self.ml_predictor = joblib.load(self.ml_model_path)
                logger.info("ML model loaded successfully")
            else:
                logger.info("ML model not provided or not found - using rule-based detection")

            # Load DL model if path provided
            if self.dl_model_path and self.dl_model_path.exists():
                if _check_tensorflow():
                    import tensorflow as tf
                    from tensorflow import keras
                    logger.info(f"Loading DL model: {self.dl_model_path}")
                    self.dl_predictor = keras.models.load_model(self.dl_model_path)
                    logger.info("DL model loaded successfully")
                else:
                    logger.warning("TensorFlow not available, DL model will not be used")
            else:
                logger.info("DL model not provided or not found - using rule-based detection")

            # Load shared preprocessing components if models are loaded
            if self.ml_predictor or self.dl_predictor:
                self._load_preprocessing_components()

            logger.info("Adaptive predictor initialized successfully (Rule-based with optional ML/DL)")

        except Exception as e:
            logger.warning(f"Failed to load models: {e} - using rule-based detection only")
            logger.info("Adaptive predictor initialized with rule-based detection")

    def _load_preprocessing_components(self):
        """Load preprocessing components (scaler, encoders, etc.)."""
        models_dir = self.ml_model_path.parent  # Use ML model directory

        # Load scaler
        scaler_path = models_dir / "scaler.joblib"
        if scaler_path.exists():
            self.scaler = joblib.load(scaler_path)
            logger.info("Loaded scaler")

        # Load label encoder
        label_encoder_path = models_dir / "label_encoder_label.joblib"
        if label_encoder_path.exists():
            self.label_encoder = joblib.load(label_encoder_path)
            logger.info("Loaded label encoder")

        # Load feature names
        feature_names_path = models_dir / "feature_names.joblib"
        if feature_names_path.exists():
            self.feature_names = joblib.load(feature_names_path)
            logger.info(f"Loaded feature names ({len(self.feature_names)} features)")

    def calculate_complexity(self, flow_features: Dict[str, float]) -> float:
        """
        Calculate complexity score for a flow using simplified features.

        Args:
            flow_features: Dictionary of flow features

        Returns:
            Complexity score (higher = more complex)
        """
        complexity = 0.0

        # Packet count complexity (log scale)
        packet_count = flow_features.get('packet_count', 0)
        if packet_count > 0:
            complexity += np.log(packet_count + 1) * 10

        # Byte count complexity (log scale)
        byte_count = flow_features.get('byte_count', 0)
        if byte_count > 0:
            complexity += np.log(byte_count + 1) * 5

        # Flow duration complexity
        duration = flow_features.get('flow_duration', 0)
        if duration > 0:
            complexity += min(duration / 10, 20)  # Cap at 20

        # Protocol complexity (TCP is more complex than UDP/ICMP)
        protocol = flow_features.get('protocol', 0)
        if protocol == 6:  # TCP
            complexity += 15
        elif protocol == 17:  # UDP
            complexity += 5
        elif protocol == 1:  # ICMP
            complexity += 2

        # Port complexity (well-known ports might indicate attacks)
        port = flow_features.get('port', 0)
        if port in [22, 23, 135, 139, 445, 1433, 3389]:  # Common attack ports
            complexity += 25

        return complexity

    def select_model(self, is_known_attack: bool) -> str:
        """
        Select appropriate model based on attack knowledge.

        Args:
            is_known_attack: True if flow matches known attack patterns

        Returns:
            Model type ('ml' or 'dl')
        """
        if is_known_attack and self.ml_predictor is not None:
            return 'ml'  # Use ML for known attack patterns
        elif self.dl_predictor is not None:
            return 'dl'  # Use DL for unknown/novel patterns
        else:
            return 'ml'  # Fallback to ML if DL not available

    def predict(self, flow_features: Dict[str, float]) -> Dict[str, any]:
        """
        Make prediction using rule-based detection for known attacks and ML/DL for unknown patterns.

        Args:
            flow_features: Dictionary of flow features

        Returns:
            Dictionary with prediction results
        """
        try:
            # Extract simplified features
            flow_duration = flow_features.get('flow_duration', 0)
            packet_count = flow_features.get('packet_count', 0)
            byte_count = flow_features.get('byte_count', 0)
            protocol = flow_features.get('protocol', 0)
            port = flow_features.get('port', 0)

            # Rule-based anomaly detection for specific known attack types
            anomaly_type = "normal"
            confidence = 0.0
            is_known_attack = False

            # DDoS Attack - High packet count and byte count
            if packet_count > 1000 and byte_count > 50000:
                anomaly_type = "DDoS Attack"
                confidence = min((packet_count + byte_count / 100) / 2000, 1.0)
                is_known_attack = True

            # Port Scan - High flow duration with low packet count
            elif flow_duration > 500 and packet_count < 10:
                anomaly_type = "Port Scan"
                confidence = min(flow_duration / 1000, 1.0)
                is_known_attack = True

            # Brute Force - High packet count with low byte count
            elif packet_count > 500 and byte_count < 1000:
                anomaly_type = "Brute Force Attack"
                confidence = min(packet_count / 1000, 1.0)
                is_known_attack = True

            # Suspicious Protocol - Unusual protocol usage
            elif protocol not in [1, 6, 17]:  # Not ICMP, TCP, or UDP
                anomaly_type = "Suspicious Protocol"
                confidence = 0.8
                is_known_attack = True

            # Suspicious Port Access - Well-known attack ports
            elif port in [22, 23, 135, 139, 445, 1433, 3389]:  # SSH, Telnet, RPC, SMB, SQL, RDP
                anomaly_type = "Suspicious Port Access"
                confidence = 0.7
                is_known_attack = True

            # High Traffic Anomaly - Very high byte count
            elif byte_count > 100000:
                anomaly_type = "High Traffic Anomaly"
                confidence = min(byte_count / 200000, 1.0)
                is_known_attack = True

            # Long Duration Flow - Suspiciously long flow
            elif flow_duration > 1000:
                anomaly_type = "Long Duration Flow"
                confidence = min(flow_duration / 2000, 1.0)
                is_known_attack = True

            # Select model based on whether it's a known attack
            model_type = self.select_model(is_known_attack)

            # Calculate complexity for logging purposes
            complexity = self.calculate_complexity(flow_features)

            # If it's a known attack detected by rules, use rule-based result
            if is_known_attack:
                result = {
                    'label': 'anomaly',
                    'score': float(confidence),
                    'anomaly_type': anomaly_type,
                    'model_type': 'rule-based',
                    'complexity': float(complexity),
                    'timestamp': time.time()
                }
                return result

            # For unknown patterns, use the selected ML/DL model
            else:
                # Convert features to array for model prediction
                if self.feature_names:
                    feature_array = self.feature_extractor.features_to_array(
                        flow_features, self.feature_names
                    )
                else:
                    feature_array = self.feature_extractor.features_to_array(flow_features)

                # Ensure correct shape
                if feature_array.ndim == 1:
                    feature_array = feature_array.reshape(1, -1)

                # Apply scaling
                if self.scaler:
                    feature_array = self.scaler.transform(feature_array)

                # Make prediction using selected model
                if model_type == 'ml' and self.ml_predictor:
                    prediction, confidence, anomaly_type = self._predict_ml(feature_array)
                elif model_type == 'dl' and self.dl_predictor:
                    prediction, confidence, anomaly_type = self._predict_dl(feature_array)
                else:
                    # Fallback to rule-based if models not available
                    anomaly_type = "normal"
                    confidence = 0.85

                result = {
                    'label': 'anomaly' if anomaly_type != 'normal' else 'normal',
                    'score': float(confidence),
                    'anomaly_type': anomaly_type,
                    'model_type': model_type,
                    'complexity': float(complexity),
                    'timestamp': time.time()
                }

                return result

        except Exception as e:
            logger.error(f"Prediction error: {e}")
            raise

    def _predict_ml(self, features: np.ndarray) -> Tuple[int, float, str]:
        """Make prediction using ML model."""
        # Predict
        prediction = self.ml_predictor.predict(features)[0]

        # Get confidence
        if hasattr(self.ml_predictor, 'predict_proba'):
            proba = self.ml_predictor.predict_proba(features)[0]
            idx = int(prediction)
            confidence = float(proba[idx]) if 0 <= idx < len(proba) else float(np.max(proba))

            # Try to get attack type from label encoder
            if self.label_encoder is not None:
                try:
                    label = self.label_encoder.inverse_transform([prediction])[0]
                    if label != 'BENIGN':
                        anomaly_type = self.attack_type_map.get(label, 'Unknown Attack')
                    else:
                        anomaly_type = 'normal'
                except:
                    anomaly_type = 'normal' if prediction == 0 else 'Unknown Attack'
            else:
                anomaly_type = 'normal' if prediction == 0 else 'Unknown Attack'
        else:
            # Hard class labels only: report full confidence in the assigned class
            confidence = 1.0
            anomaly_type = 'normal' if prediction == 0 else 'Unknown Attack'

        return int(prediction), float(confidence), anomaly_type

    def _predict_dl(self, features: np.ndarray) -> Tuple[int, float, str]:
        """Make prediction using DL model."""
        if not _check_tensorflow() or self.dl_predictor is None:
            raise RuntimeError("DL model not available")

        import tensorflow as tf
        import numpy as np

        # Reshape for LSTM input (samples, timesteps, features)
        if hasattr(self.dl_predictor, 'input_shape') and len(self.dl_predictor.input_shape) == 3:
            # LSTM expects (batch_size, timesteps, features)
            features_reshaped = features.reshape((features.shape[0], 1, features.shape[1]))
        else:
            features_reshaped = features

        # Predict
        prediction_proba = self.dl_predictor.predict(features_reshaped, verbose=0)[0]

        # Handle different output shapes
        if len(prediction_proba.shape) == 0:
            # Single value (sigmoid): value is P(anomaly); score = confidence in predicted label
            p_anomaly = float(prediction_proba)
            prediction = 1 if p_anomaly > 0.5 else 0
            confidence = p_anomaly if prediction == 1 else (1.0 - p_anomaly)
        else:
            # Softmax: confidence for the predicted class index
            prediction = int(np.argmax(prediction_proba))
            confidence = float(prediction_proba[prediction])

        # Determine anomaly type (simplified for DL models)
        anomaly_type = 'normal' if prediction == 0 else 'Unknown Attack'

        return int(prediction), float(confidence), anomaly_type

    def predict_batch(self, flows_features: List[Dict[str, float]]) -> List[Dict[str, any]]:
        """
        Make predictions on multiple flows.

        Args:
            flows_features: List of feature dictionaries

        Returns:
            List of prediction results
        """
        results = []
        for features in flows_features:
            try:
                result = self.predict(features)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in batch prediction: {e}")
                continue

        return results

    def get_stats(self) -> Dict[str, any]:
        """
        Get predictor statistics.

        Returns:
            Dictionary with predictor stats
        """
        return {
            'ml_model_loaded': self.ml_predictor is not None,
            'dl_model_loaded': self.dl_predictor is not None,
            'complexity_threshold': self.complexity_threshold,
            'ml_model_path': str(self.ml_model_path),
            'dl_model_path': str(self.dl_model_path)
        }