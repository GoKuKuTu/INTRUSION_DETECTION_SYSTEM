#!/usr/bin/env python3
"""
Real-Time Prediction Service

This module loads ML models once and performs real-time predictions
on streaming network flow data.

Features:
- Model loading and caching
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


class RealtimePredictor:
    """
    Real-time prediction service for network anomaly detection.
    """
    
    def __init__(self, model_path: str, model_type: str = 'ml'):
        """
        Initialize real-time predictor.
        
        Args:
            model_path: Path to the model file
            model_type: Type of model ('ml' or 'dl')
        """
        self.model_path = Path(model_path)
        self.model_type = model_type
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.feature_names = None
        self.feature_extractor = FeatureExtractor()
        self.model_loaded = False
        
        # Attack type mapping (based on prediction patterns)
        self.attack_type_map = {
            'BENIGN': 'normal',
            'DDoS': 'DDoS Attack',
            'PortScan': 'Port Scan',
            'DataExfiltration': 'Data Exfiltration',
            'BruteForce': 'Brute Force Attack',
            'Malware': 'Malware',
        }
        
        logger.info(f"Initializing RealtimePredictor with {model_type} model: {model_path}")
        self._load_model()
    
    def _load_model(self):
        """Load model and preprocessing components."""
        try:
            if not self.model_path.exists():
                raise FileNotFoundError(f"Model file not found: {self.model_path}")
            
            if self.model_type == 'ml':
                self._load_ml_model()
            else:
                self._load_dl_model()
            
            self._load_preprocessing_components()
            self.model_loaded = True
            logger.info("Model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            raise
    
    def _load_ml_model(self):
        """Load machine learning model."""
        try:
            logger.info(f"Loading ML model from {self.model_path}")
            self.model = joblib.load(self.model_path)
            logger.info("ML model loaded")
        except Exception as e:
            logger.error(f"Error loading ML model: {e}")
            raise
    
    def _load_dl_model(self):
        """Load deep learning model."""
        if not _check_tensorflow():
            raise ImportError("TensorFlow not available for DL models")
        import tensorflow as tf
        from tensorflow import keras
        
        try:
            logger.info(f"Loading DL model from {self.model_path}")
            self.model = keras.models.load_model(self.model_path)
            logger.info("DL model loaded")
        except Exception as e:
            logger.error(f"Error loading DL model: {e}")
            raise
    
    def _load_preprocessing_components(self):
        """Load preprocessing components (scaler, encoders, etc.)."""
        models_dir = self.model_path.parent
        
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
    
    def predict(self, flow_features: Dict[str, float]) -> Dict[str, any]:
        """
        Make prediction on flow features.
        
        Args:
            flow_features: Dictionary of flow features
            
        Returns:
            Dictionary with prediction results:
            - label: 'normal' or 'anomaly'
            - score: confidence score (0-1)
            - anomaly_type: Type of attack (if anomaly)
            - model_type: Type of model used
        """
        if not self.model_loaded:
            raise RuntimeError("Model not loaded")
        
        try:
            # Convert features to array
            if self.feature_names:
                feature_array = self.feature_extractor.features_to_array(
                    flow_features, self.feature_names
                )
            else:
                feature_array = self.feature_extractor.features_to_array(flow_features)
            
            # Ensure correct shape
            if feature_array.ndim == 1:
                feature_array = feature_array.reshape(1, -1)
            
            # Align feature count if needed
            if self.scaler:
                expected_len = self.scaler.mean_.shape[0]
                if feature_array.shape[1] < expected_len:
                    padded = np.zeros((1, expected_len), dtype=float)
                    padded[:, :feature_array.shape[1]] = feature_array
                    feature_array = padded
                elif feature_array.shape[1] > expected_len:
                    feature_array = feature_array[:, :expected_len]
            
            # Apply scaling
            if self.scaler:
                feature_array = self.scaler.transform(feature_array)
            
            # Make prediction
            if self.model_type == 'ml':
                prediction, confidence, anomaly_type = self._predict_ml(feature_array)
            else:
                prediction, confidence, anomaly_type = self._predict_dl(feature_array)
            
            result = {
                'label': 'anomaly' if prediction == 1 else 'normal',
                'score': float(confidence),
                'anomaly_type': anomaly_type,
                'model_type': self.model_type,
                'timestamp': time.time()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            raise
    
    def _predict_ml(self, features: np.ndarray) -> Tuple[int, float, str]:
        """Make prediction using ML model."""
        # Predict
        prediction = self.model.predict(features)[0]
        
        # Get confidence
        if hasattr(self.model, 'predict_proba'):
            proba = self.model.predict_proba(features)[0]
            confidence = np.max(proba)
            
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
            confidence = 1.0 if prediction == 1 else 0.0
            anomaly_type = 'normal' if prediction == 0 else 'Unknown Attack'
        
        return int(prediction), float(confidence), anomaly_type
    
    def _predict_dl(self, features: np.ndarray) -> Tuple[int, float, str]:
        """Make prediction using DL model."""
        if not _check_tensorflow():
            raise RuntimeError("TensorFlow not available")
        import tensorflow as tf
        import numpy as np
        
        # Predict
        prediction_proba = self.model.predict(features, verbose=0)[0]
        
        # Handle different output shapes
        if len(prediction_proba.shape) == 0:
            # Single value (sigmoid output)
            confidence = float(prediction_proba)
            prediction = 1 if confidence > 0.5 else 0
        else:
            # Multiple values (softmax output)
            prediction = np.argmax(prediction_proba)
            confidence = float(np.max(prediction_proba))
        
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

