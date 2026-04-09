#!/usr/bin/env python3
"""
Network Anomaly Detection - FastAPI Model Serving API

This FastAPI application provides a REST API for serving machine learning and
deep learning models for network anomaly detection. It supports both ML and DL
models with automatic preprocessing and model loading.

Features:
- POST /predict endpoint for model inference
- Support for both ML (scikit-learn) and DL (TensorFlow/Keras) models
- Automatic preprocessing with saved scalers and encoders
- Pydantic request validation
- OpenAPI documentation with examples
- Local development server with uvicorn

Usage:
    python src/api.py  # Start local server
    curl -X POST "http://localhost:8001/predict" -H "Content-Type: application/json" -d '{"features": [1,2,3,...]}'
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Union, Optional
import warnings
import asyncio

# FastAPI imports
try:
    from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
    from fastapi import BackgroundTasks
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, Field, validator
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False
    logging.error("FastAPI not available. Install with: pip install fastapi uvicorn")

# Machine Learning imports
try:
    import joblib
    import numpy as np
    import pandas as pd
    from sklearn.preprocessing import StandardScaler, LabelEncoder
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logging.error("ML libraries not available. Install with: pip install scikit-learn")

# Deep Learning imports
try:
    import tensorflow as tf
    from tensorflow import keras
    DL_AVAILABLE = True
except Exception as e:
    DL_AVAILABLE = False
    logging.warning(f"TensorFlow not available: {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress warnings
warnings.filterwarnings('ignore')

# Initialize FastAPI app
if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="Network Anomaly Detection API",
        description="REST API for network anomaly detection using ML and DL models",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    # CORS for local frontend (Vite on 5173) and common localhost variants
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"]
    )
else:
    app = None


class FeatureRequest(BaseModel):
    """
    Request model for feature-based prediction.
    
    Accepts either a list of feature values or a dictionary of named features.
    """
    features: Union[List[float], Dict[str, float]] = Field(
        ...,
        description="Feature values as a list or dictionary",
        example=[1.0, 2.0, 3.0, 4.0, 5.0]
    )
    
    @validator('features')
    def validate_features(cls, v):
        """Validate that features are provided and numeric."""
        if isinstance(v, list):
            if len(v) == 0:
                raise ValueError("Features list cannot be empty")
            if not all(isinstance(x, (int, float)) for x in v):
                raise ValueError("All features must be numeric")
        elif isinstance(v, dict):
            if len(v) == 0:
                raise ValueError("Features dictionary cannot be empty")
            if not all(isinstance(x, (int, float)) for x in v.values()):
                raise ValueError("All feature values must be numeric")
        return v


class PredictionResponse(BaseModel):
    """
    Response model for prediction results.
    """
    label: str = Field(..., description="High-level label: 'normal' or 'anomaly'")
    score: float = Field(..., description="Prediction confidence score (0-1)")
    model: str = Field(..., description="Name of the model used for prediction")
    model_type: str = Field(..., description="Type of model: 'ml' or 'dl'")
    is_anomaly: bool = Field(
        ..., description="True if the traffic is predicted as anomalous"
    )
    anomaly_type: str = Field(
        ...,
        description=(
            "Specific attack / anomaly class if available (e.g., 'DDoS', 'PortScan'); "
            "'normal' when no attack is detected"
        ),
    )


class ModelLoader:
    """
    Model loader for both ML and DL models with preprocessing support.
    """
    
    def __init__(self):
        self.ml_model = None
        self.dl_model = None
        self.scaler = None
        self.label_encoder = None
        self.feature_names = None
        self.model_metadata = None
    
    def load_ml_model(self, model_path: str) -> bool:
        """
        Load machine learning model and preprocessing components.
        
        Args:
            model_path (str): Path to the ML model file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Loading ML model from {model_path}")

            # Try primary path
            def _load_from(path: Path) -> bool:
                self.ml_model = joblib.load(path)

                # Load preprocessing components from models directory
                models_dir = path.parent

                scaler_path = models_dir / "scaler.joblib"
                if scaler_path.exists():
                    self.scaler = joblib.load(scaler_path)
                    logger.info("Loaded scaler")

                label_encoder_path = models_dir / "label_encoder_label.joblib"
                if label_encoder_path.exists():
                    self.label_encoder = joblib.load(label_encoder_path)
                    logger.info("Loaded label encoder")

                feature_names_path = models_dir / "feature_names.joblib"
                if feature_names_path.exists():
                    self.feature_names = joblib.load(feature_names_path)
                    logger.info("Loaded feature names")

                try:
                    metadata_path = Path(path).with_name(Path(path).stem + "_metadata.joblib")
                    if metadata_path.exists():
                        self.model_metadata = joblib.load(metadata_path)
                        logger.info("Loaded model metadata")
                except Exception as meta_err:
                    logger.warning(f"Metadata load skipped: {meta_err}")

                logger.info(f"ML model loaded successfully from {path}")
                return True

            primary = Path(model_path)
            try:
                return _load_from(primary)
            except Exception as primary_err:
                logger.error(f"Primary model load failed: {primary_err}")

            # Fallback candidates
            candidates = [
                Path("models/full_model.pkl"),
                Path("models/time_split_model.pkl"),
                Path("models/ml_best.pkl"),
            ]
            for cand in candidates:
                try:
                    if cand.exists() and cand.resolve() != primary.resolve():
                        logger.info(f"Attempting fallback model load from {cand}")
                        return _load_from(cand)
                except Exception as cand_err:
                    logger.error(f"Fallback load failed for {cand}: {cand_err}")

            return False
        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            return False
    
    def load_dl_model(self, model_path: str) -> bool:
        """
        Load deep learning model.
        
        Args:
            model_path (str): Path to the DL model file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not DL_AVAILABLE:
                logger.error("TensorFlow not available for DL model loading")
                return False
            
            logger.info(f"Loading DL model from {model_path}")
            self.dl_model = keras.models.load_model(model_path)
            logger.info("DL model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load DL model: {e}")
            return False
    
    def preprocess_features(self, features: Union[List[float], Dict[str, float]], 
                          model_type: str) -> np.ndarray:
        """
        Preprocess input features for model prediction.
        
        Args:
            features: Input features as list or dict
            model_type: Type of model ('ml' or 'dl')
            
        Returns:
            np.ndarray: Preprocessed features
        """
        try:
            # Convert to numpy array
            if isinstance(features, dict):
                if self.feature_names is not None:
                    # Use feature names to order features
                    ordered = [features.get(name, 0.0) for name in self.feature_names]
                    feature_array = np.array(ordered, dtype=float)
                else:
                    feature_array = np.array(list(features.values()), dtype=float)
            else:
                feature_array = np.array(features, dtype=float)

            # If ML model expects a specific number of features, align length by padding/trimming
            if model_type == 'ml' and self.feature_names is not None:
                expected_len = len(self.feature_names)
                if feature_array.ndim == 1:
                    if feature_array.size < expected_len:
                        padded = np.zeros(expected_len, dtype=float)
                        padded[: feature_array.size] = feature_array
                        feature_array = padded
                    elif feature_array.size > expected_len:
                        feature_array = feature_array[:expected_len]

            # Reshape for single prediction
            feature_array = feature_array.reshape(1, -1)

            # Apply scaling if available
            if self.scaler is not None and model_type == 'ml':
                try:
                    feature_array = self.scaler.transform(feature_array)
                except Exception as e:
                    # Attempt to align scaler input size by recreating zeros of expected scaler shape
                    try:
                        expected_len = self.scaler.mean_.shape[0]
                        x = feature_array
                        if x.shape[1] < expected_len:
                            tmp = np.zeros((1, expected_len), dtype=float)
                            tmp[:, : x.shape[1]] = x
                            x = tmp
                        elif x.shape[1] > expected_len:
                            x = x[:, :expected_len]
                        feature_array = self.scaler.transform(x)
                    except Exception:
                        raise

            return feature_array

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Feature preprocessing failed: {e}")
            raise HTTPException(status_code=400, detail=f"Feature preprocessing failed: {e}")
    
    def predict_ml(self, features: np.ndarray) -> tuple:
        """
        Make prediction using ML model.
        
        Args:
            features: Preprocessed features
            
        Returns:
            tuple: (prediction, confidence_score)
        """
        try:
            # Make prediction
            prediction = self.ml_model.predict(features)[0]
            
            # Get prediction probability if available
            if hasattr(self.ml_model, 'predict_proba'):
                proba = self.ml_model.predict_proba(features)[0]
                confidence = np.max(proba)
            else:
                confidence = 1.0 if prediction == 1 else 0.0
            
            return prediction, confidence
            
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            raise HTTPException(status_code=500, detail=f"ML prediction failed: {e}")
    
    def predict_dl(self, features: np.ndarray) -> tuple:
        """
        Make prediction using DL model.
        
        Args:
            features: Preprocessed features
            
        Returns:
            tuple: (prediction, confidence_score)
        """
        try:
            if not DL_AVAILABLE:
                raise HTTPException(status_code=500, detail="TensorFlow not available")
            
            # Make prediction
            prediction_proba = self.dl_model.predict(features, verbose=0)[0]
            
            # For binary classification
            if len(prediction_proba.shape) == 0:
                # Single value (sigmoid output)
                confidence = float(prediction_proba)
                prediction = 1 if confidence > 0.5 else 0
            else:
                # Multiple values (softmax output)
                prediction = np.argmax(prediction_proba)
                confidence = float(np.max(prediction_proba))
            
            return prediction, confidence
            
        except Exception as e:
            logger.error(f"DL prediction failed: {e}")
            raise HTTPException(status_code=500, detail=f"DL prediction failed: {e}")


# Global model loader instance
model_loader = ModelLoader()


def choose_model_for_features(
    features: Union[List[float], Dict[str, float]]
) -> tuple[str, str]:
    """
    Simple heuristic to choose between ML and DL models.

    - Use ML for simpler / low-variance feature patterns
    - Use DL for more complex / high-variance patterns, but only if a DL
      model file is available and TensorFlow is installed.

    Returns:
        (model_type, model_path)
    """
    # Default model paths
    ml_path = Path("models/ml_best.pkl")
    dl_path = Path("models/dl_lstm.h5")

    # If DL is not available or file missing, always fall back to ML
    dl_usable = DL_AVAILABLE and dl_path.exists()

    # Convert features to numpy array for a basic complexity metric
    if isinstance(features, dict):
        values = np.array(list(features.values()), dtype=float)
    else:
        values = np.array(features, dtype=float)

    if values.size == 0 or not dl_usable:
        return "ml", str(ml_path)

    # Heuristic: combine standard deviation and maximum magnitude
    std = float(np.std(values))
    max_val = float(np.max(np.abs(values)))
    complexity_score = std + 0.001 * max_val

    # Threshold chosen empirically for typical flow features; can be tuned.
    # For small, stable flows -> ML; for spiky / large-magnitude flows -> DL.
    if complexity_score > 50.0:
        logger.info(
            f"Auto model selection: using DL (complexity={complexity_score:.2f}, std={std:.2f}, max={max_val:.2f})"
        )
        return "dl", str(dl_path)

    logger.info(
        f"Auto model selection: using ML (complexity={complexity_score:.2f}, std={std:.2f}, max={max_val:.2f})"
    )
    return "ml", str(ml_path)


# ---------------------------------------------------------------------------
# Real-time streaming support (inspired by real-time IDS architectures)
# ---------------------------------------------------------------------------

# Connected WebSocket clients
active_clients: List[WebSocket] = []

# Flag to control background real-time loop
realtime_running: bool = False


async def predict_from_features_async(
    features: List[float],
    model: str = "ml",
    path: str = "models/ml_best.pkl",
) -> PredictionResponse:
    """
    Async helper to run a prediction using the existing model pipeline.
    This reuses the same logic as the /predict endpoint.
    """
    # Determine effective model and path, supporting 'auto'
    if model == "auto":
        effective_model, effective_path = choose_model_for_features(features)
    else:
        effective_model, effective_path = model, path

    if effective_model not in ["ml", "dl"]:
        raise HTTPException(
            status_code=400, detail="Model type must be 'ml', 'dl', or 'auto'"
        )

    model_path = Path(effective_path)
    if not model_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Model file not found: {effective_path}"
        )

    # Load model if not already loaded
    model_loaded = False
    if effective_model == "ml":
        if model_loader.ml_model is None:
            model_loaded = model_loader.load_ml_model(str(model_path))
        else:
            model_loaded = True
    else:
        if model_loader.dl_model is None:
            model_loaded = model_loader.load_dl_model(str(model_path))
        else:
            model_loaded = True

    if not model_loaded:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load {effective_model} model from {effective_path}",
        )

    # Preprocess and predict
    processed_features = model_loader.preprocess_features(features, effective_model)
    if effective_model == "ml":
        prediction, confidence = model_loader.predict_ml(processed_features)
    else:
        prediction, confidence = model_loader.predict_dl(processed_features)

    # Convert prediction to high-level label and specific anomaly type
    original_label = None
    if effective_model == "ml" and model_loader.label_encoder is not None:
        try:
            original_label = model_loader.label_encoder.inverse_transform(
                [prediction]
            )[0]
            is_anomaly = original_label != "BENIGN"
        except Exception:
            is_anomaly = prediction == 1
    else:
        is_anomaly = prediction == 1

    label = "anomaly" if is_anomaly else "normal"
    if is_anomaly and original_label:
        anomaly_type = original_label
    else:
        anomaly_type = "normal"

    # Determine model name
    model_name = model_path.stem
    if model_loader.model_metadata and "model_name" in model_loader.model_metadata:
        model_name = model_loader.model_metadata["model_name"]

    logger.info(
        f"[realtime] Prediction: {label} (type={anomaly_type}), "
        f"confidence: {confidence:.4f}, model: {model_name}"
    )

    return PredictionResponse(
        label=label,
        score=float(confidence),
        model=model_name,
        model_type=effective_model,
        is_anomaly=is_anomaly,
        anomaly_type=anomaly_type,
    )


async def realtime_loop():
    """
    Background loop that simulates streaming network flows, performs
    model inference, and broadcasts results to connected WebSocket clients.
    """
    global realtime_running

    logger.info("Real-time loop started")
    try:
        while realtime_running:
            # Example synthetic feature vector; align dimensions with training features.
            features = [
                100.0,  # flow duration
                50.0,   # packet count
                1024.0, # byte count
                1.0,    # protocol type
                80.0,   # port number
            ]

            try:
                prediction = await predict_from_features_async(
                    features, model="auto", path="models/ml_best.pkl"
                )
            except Exception as e:
                logger.error(f"Real-time prediction failed: {e}")
                await asyncio.sleep(1.0)
                continue

            # Broadcast to all connected WebSocket clients
            payload = {
                "features": features,
                "prediction": prediction.dict(),
            }

            stale_clients: List[WebSocket] = []
            for ws in active_clients:
                try:
                    await ws.send_json(payload)
                except Exception as ws_err:
                    logger.warning(f"WebSocket send failed, marking client stale: {ws_err}")
                    stale_clients.append(ws)

            # Remove stale clients
            for ws in stale_clients:
                try:
                    await ws.close()
                except Exception:
                    pass
                if ws in active_clients:
                    active_clients.remove(ws)

            # Control streaming rate (1 event per second)
            await asyncio.sleep(1.0)
    finally:
        logger.info("Real-time loop stopped")


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Network Anomaly Detection API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", response_model=Dict[str, str])
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "API is running"}


@app.post("/predict", response_model=PredictionResponse)
async def predict(
    request: FeatureRequest,
    model: str = Query(
        "auto",
        description="Model type: 'ml', 'dl', or 'auto' for automatic selection",
    ),
    path: str = Query(
        "models/ml_best.pkl", description="Path to the model file (for 'ml' or 'dl')"
    ),
):
    """
    Predict network anomaly using the specified model.
    
    Args:
        request: Feature request with input data
        model: Model type ('ml' for machine learning, 'dl' for deep learning)
        path: Path to the model file
        
    Returns:
        PredictionResponse: Prediction results with label, score, and model info
    """
    try:
        # Determine effective model and model path, supporting 'auto'
        if model == "auto":
            effective_model, effective_path = choose_model_for_features(
                request.features
            )
        else:
            effective_model, effective_path = model, path

        if effective_model not in ["ml", "dl"]:
            raise HTTPException(
                status_code=400,
                detail="Model type must be 'ml', 'dl', or 'auto'",
            )

        # Check if model file exists
        model_path = Path(effective_path)
        if not model_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Model file not found: {effective_path}",
            )

        # Load model if not already loaded
        model_loaded = False
        if effective_model == "ml":
            if model_loader.ml_model is None or str(model_loader.ml_model) != str(
                model_path
            ):
                model_loaded = model_loader.load_ml_model(str(model_path))
        else:
            if model_loader.dl_model is None or str(model_loader.dl_model) != str(
                model_path
            ):
                model_loaded = model_loader.load_dl_model(str(model_path))

        if not model_loaded:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to load {effective_model} model from {effective_path}",
            )

        # Preprocess features
        processed_features = model_loader.preprocess_features(
            request.features, effective_model
        )

        # Make prediction
        if effective_model == "ml":
            prediction, confidence = model_loader.predict_ml(processed_features)
        else:
            prediction, confidence = model_loader.predict_dl(processed_features)
        
        # Convert prediction to label and anomaly type
        original_label = None
        if effective_model == 'ml' and model_loader.label_encoder is not None:
            # Use label encoder to get original label
            try:
                original_label = model_loader.label_encoder.inverse_transform([prediction])[0]
                is_anomaly = original_label != 'BENIGN'
            except Exception:
                is_anomaly = prediction == 1
        else:
            # Binary classification: 0 = normal, 1 = anomaly
            is_anomaly = prediction == 1
        
        label = "anomaly" if is_anomaly else "normal"
        if is_anomaly and original_label:
            anomaly_type = original_label
        else:
            anomaly_type = "normal"
        
        # Get model name
        model_name = model_path.stem
        if model_loader.model_metadata and 'model_name' in model_loader.model_metadata:
            model_name = model_loader.model_metadata['model_name']
        
        logger.info(
            f"Prediction: {label} (type={anomaly_type}), "
            f"confidence: {confidence:.4f}, model: {model_name}"
        )
        
        return PredictionResponse(
            label=label,
            score=float(confidence),
            model=model_name,
            model_type=effective_model,
            is_anomaly=is_anomaly,
            anomaly_type=anomaly_type,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@app.get("/models", response_model=Dict[str, List[str]])
async def list_models():
    """List available models in the models directory."""
    try:
        models_dir = Path("models")
        if not models_dir.exists():
            return {"ml_models": [], "dl_models": []}
        
        ml_models = []
        dl_models = []
        
        for model_file in models_dir.glob("*"):
            if model_file.suffix == '.pkl':
                ml_models.append(str(model_file))
            elif model_file.suffix == '.h5':
                dl_models.append(str(model_file))
        
        return {
            "ml_models": ml_models,
            "dl_models": dl_models
        }
        
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list models: {e}")


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    """
    WebSocket endpoint for real-time IDS updates.

    Clients receive a continuous stream of feature vectors and predictions
    produced by the background real-time loop.
    """
    await ws.accept()
    active_clients.append(ws)
    logger.info("WebSocket client connected")

    try:
        # Keep connection open; we do not require client messages.
        while True:
            # We only care that the client is still alive; ignore incoming data.
            await ws.receive_text()
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
    finally:
        if ws in active_clients:
            active_clients.remove(ws)


@app.post("/realtime/start", response_model=Dict[str, str])
async def start_realtime(background_tasks: BackgroundTasks):
    """
    Start the background real-time IDS loop.
    """
    global realtime_running
    if not realtime_running:
        realtime_running = True
        background_tasks.add_task(realtime_loop)
        logger.info("Real-time IDS started")
        return {"status": "started"}
    return {"status": "already_running"}


@app.post("/realtime/stop", response_model=Dict[str, str])
async def stop_realtime():
    """
    Stop the background real-time IDS loop.
    """
    global realtime_running
    if realtime_running:
        realtime_running = False
        logger.info("Real-time IDS stop requested")
        return {"status": "stopping"}
    return {"status": "not_running"}


def main():
    """
    Main function to run the FastAPI server.
    """
    if not FASTAPI_AVAILABLE:
        print("FastAPI not available. Install with: pip install fastapi uvicorn")
        return 1
    
    print("Starting Network Anomaly Detection API server...")
    print("API Documentation: http://localhost:8001/docs")
    print("Alternative Docs: http://localhost:8001/redoc")
    print("Health Check: http://localhost:8001/health")
    print()
    
    # Run the server
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8001,
        reload=False,  # Disable reload to avoid import issues
        log_level="info"
    )


if __name__ == "__main__":
    # Example usage and curl commands
    print("Network Anomaly Detection - FastAPI Model Serving API")
    print("="*60)
    print()
    print("Example curl commands:")
    print()
    print("1. Predict with ML model (default):")
    print('curl -X POST "http://localhost:8001/predict" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"features": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]}\'')
    print()
    print("2. Predict with DL model:")
    print('curl -X POST "http://localhost:8001/predict?model=dl&path=models/dl_lstm.h5" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"features": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]}\'')
    print()
    print("3. Predict with named features:")
    print('curl -X POST "http://localhost:8001/predict" \\')
    print('  -H "Content-Type: application/json" \\')
    print('  -d \'{"features": {"src_port": 80, "dst_port": 443, "protocol": 1, "flow_duration": 100}}\'')
    print()
    print("4. List available models:")
    print('curl -X GET "http://localhost:8001/models"')
    print()
    print("5. Health check:")
    print('curl -X GET "http://localhost:8001/health"')
    print()
    print("="*60)
    print()
    
    exit(main())
