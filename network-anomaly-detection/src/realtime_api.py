#!/usr/bin/env python3
"""
Real-Time Intrusion Detection System API

Flask API with WebSocket support for real-time network anomaly detection.
Provides REST endpoints and Socket.IO for streaming predictions.

Features:
- Real-time /predict endpoint
- WebSocket streaming of predictions
- Attack logging
- Alert system
"""

import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json

try:
    from flask import Flask, request, jsonify
    from flask_cors import CORS
    from flask_socketio import SocketIO, emit
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    logging.error("Flask not available. Install with: pip install flask flask-cors flask-socketio")

# Import modules - handle both direct import and relative import
try:
    from traffic_capture import TrafficCapture
    from feature_extractor import FeatureExtractor
    from adaptive_predictor import AdaptiveRealtimePredictor
except ImportError:
    from .traffic_capture import TrafficCapture
    from .feature_extractor import FeatureExtractor
    from .adaptive_predictor import AdaptiveRealtimePredictor

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize Flask app
if FLASK_AVAILABLE:
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'network-ids-secret-key'
    CORS(app, resources={r"/*": {"origins": "*"}})
    # Try eventlet first, fallback to threading
    try:
        import eventlet
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet', logger=True, engineio_logger=True)
    except ImportError:
        socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading', logger=True, engineio_logger=True)
else:
    app = None
    socketio = None


class AttackLogger:
    """
    Logs detected attacks with timestamp, IPs, and attack type.
    """
    
    def __init__(self, log_file: str = "logs/attacks.log"):
        """Initialize attack logger."""
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Attack logger initialized: {self.log_file}")
    
    def log_attack(self, prediction: Dict, flow_features: Dict):
        """
        Log a detected attack.
        
        Args:
            prediction: Prediction result dictionary
            flow_features: Original flow features
        """
        if prediction['label'] != 'anomaly':
            return
        
        try:
            timestamp = datetime.now().isoformat()
            log_entry = {
                'timestamp': timestamp,
                'src_ip': flow_features.get('src_ip', 'unknown'),
                'dst_ip': flow_features.get('dst_ip', 'unknown'),
                'src_port': flow_features.get('src_port', 0),
                'dst_port': flow_features.get('dst_port', 0),
                'attack_type': prediction.get('anomaly_type', 'Unknown Attack'),
                'confidence': prediction.get('score', 0.0),
                'model_type': prediction.get('model_type', 'unknown')
            }
            
            # Write to log file
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
            
            logger.warning(f"ATTACK DETECTED: {log_entry['attack_type']} from {log_entry['src_ip']} to {log_entry['dst_ip']}")
            
        except Exception as e:
            logger.error(f"Error logging attack: {e}")


class RealtimeIDS:
    """
    Real-time Intrusion Detection System coordinator.
    """
    
    def __init__(self, ml_model_path: str, dl_model_path: str, complexity_threshold: float = 50.0, interface: Optional[str] = None):
        """
        Initialize real-time IDS with adaptive predictor.
        
        Args:
            ml_model_path: Path to ML model
            dl_model_path: Path to DL model
            complexity_threshold: Threshold for model selection (> threshold uses DL)
            interface: Network interface for capture
        """
        self.predictor = AdaptiveRealtimePredictor(ml_model_path, dl_model_path, complexity_threshold)
        self.feature_extractor = FeatureExtractor()
        self.traffic_capture = TrafficCapture(interface=interface)
        self.attack_logger = AttackLogger()
        self.running = False
        self.processing_thread = None
        
        logger.info("RealtimeIDS initialized with adaptive predictor")
    
    def start(self):
        """Start real-time IDS."""
        if self.running:
            logger.warning("IDS already running")
            return
        
        self.running = True
        self.traffic_capture.start()
        if socketio:
            self.processing_thread = socketio.start_background_task(self._processing_loop)
        else:
            self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
            self.processing_thread.start()
        
        logger.info("Real-time IDS started")
    
    def stop(self):
        """Stop real-time IDS."""
        self.running = False
        self.traffic_capture.stop()
        if self.processing_thread and hasattr(self.processing_thread, 'join'):
            try:
                self.processing_thread.join(timeout=2)
            except Exception:
                pass
        logger.info("Real-time IDS stopped")
    
    def _processing_loop(self):
        """Main processing loop for real-time predictions."""
        last_status_time = 0
        
        while self.running:
            try:
                current_time = time.time()
                
                # Emit status update every second
                if current_time - last_status_time >= 1.0:
                    heartbeat_data = {
                        'message': 'Monitoring heartbeat',
                        'ids_running': self.running,
                        'active_flows': self.traffic_capture.get_flow_count(),
                        'data_source': self.traffic_capture.get_data_source_type(),
                        'timestamp': current_time,
                        'heartbeat': True
                    }
                    if socketio:
                        socketio.emit('status', heartbeat_data, broadcast=True)
                        socketio.emit('heartbeat', heartbeat_data, broadcast=True)
                        logger.info('Emitted periodic heartbeat update')
                    last_status_time = current_time
                
                # Get expired flows (completed flows)
                flow = self.traffic_capture.get_expired_flow(timeout=1.0)
                
                if flow:
                    # Extract features
                    features = self.feature_extractor.extract_features(flow)
                    
                    # Make prediction
                    prediction = self.predictor.predict(features)
                    
                    # Log attack if detected
                    if prediction['label'] == 'anomaly':
                        self.attack_logger.log_attack(prediction, features)
                    
                    # Emit prediction via WebSocket
                    prediction_data = {
                        **prediction,
                        'src_ip': flow.src_ip,
                        'dst_ip': flow.dst_ip,
                        'src_port': flow.src_port,
                        'dst_port': flow.dst_port,
                        'protocol': flow.protocol,
                        'flow_duration': flow.get_duration(),
                        'total_packets': flow.fwd_packets + flow.bwd_packets,
                        'total_bytes': flow.fwd_bytes + flow.bwd_bytes,
                        'complexity': prediction.get('complexity', 0.0),
                        'data_source': self.traffic_capture.get_data_source_type()
                    }
                    
                    if socketio:
                        socketio.emit('prediction', prediction_data, broadcast=True)
                        logger.info('Broadcasted prediction event to connected clients')
                
                # Small sleep to prevent CPU spinning
                if socketio:
                    socketio.sleep(0.1)
                else:
                    time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                if socketio:
                    socketio.sleep(1)
                else:
                    time.sleep(1)
    
    def predict_single(self, flow_features: Dict[str, float]) -> Dict:
        """
        Predict on a single flow feature set.
        
        Args:
            flow_features: Flow features dictionary
            
        Returns:
            Prediction result
        """
        prediction = self.predictor.predict(flow_features)
        
        # Log if attack
        if prediction['label'] == 'anomaly':
            self.attack_logger.log_attack(prediction, flow_features)
        
        return prediction


# Global IDS instance
realtime_ids: Optional[RealtimeIDS] = None


@app.route('/', methods=['GET'])
def root():
    """Root endpoint."""
    return jsonify({
        'message': 'Real-Time Intrusion Detection System API',
        'version': '2.0.0',
        'endpoints': {
            '/predict': 'POST - Real-time prediction endpoint',
            '/health': 'GET - Health check',
            '/stats': 'GET - System statistics',
            '/attacks': 'GET - Recent attack logs'
        }
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    predictor_stats = realtime_ids.predictor.get_stats() if realtime_ids else {}
    
    return jsonify({
        'status': 'healthy',
        'ids_running': realtime_ids.running if realtime_ids else False,
        'ml_model_loaded': predictor_stats.get('ml_model_loaded', False),
        'dl_model_loaded': predictor_stats.get('dl_model_loaded', False),
        'complexity_threshold': predictor_stats.get('complexity_threshold', 50.0)
    })


@app.route('/predict', methods=['POST'])
def predict():
    """
    Real-time prediction endpoint.
    
    Accepts flow features and returns prediction.
    """
    try:
        data = request.get_json()
        
        if not data or 'features' not in data:
            return jsonify({'error': 'Missing features in request'}), 400
        
        features = data['features']
        
        if not isinstance(features, dict):
            return jsonify({'error': 'Features must be a dictionary'}), 400
        
        if not realtime_ids:
            return jsonify({'error': 'IDS not initialized'}), 500
        
        # Make prediction
        prediction = realtime_ids.predict_single(features)
        
        return jsonify(prediction)
        
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/stats', methods=['GET'])
def stats():
    """Get system statistics."""
    if not realtime_ids:
        return jsonify({'error': 'IDS not initialized'}), 500
    
    stats_data = realtime_ids.predictor.get_stats()
    stats_data.update({
        'active_flows': realtime_ids.traffic_capture.get_flow_count(),
        'ids_running': realtime_ids.running
    })
    
    return jsonify(stats_data)


@app.route('/attacks', methods=['GET'])
def get_attacks():
    """Get recent attack logs."""
    try:
        log_file = Path("logs/attacks.log")
        if not log_file.exists():
            return jsonify({'attacks': []})
        
        attacks = []
        with open(log_file, 'r') as f:
            lines = f.readlines()
            # Get last 100 attacks
            for line in lines[-100:]:
                try:
                    attacks.append(json.loads(line.strip()))
                except:
                    continue
        
        return jsonify({'attacks': attacks[-50:]})  # Return last 50

    except Exception as e:
        logger.error(f"Error reading attacks: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/emit_test', methods=['GET', 'POST'])
def emit_test():
    """Emit a synthetic prediction event to connected Socket.IO clients.

    Use this endpoint to quickly verify frontend reception of `prediction` events.
    """
    sample = {
        'label': 'anomaly',
        'anomaly_type': 'Synthetic Test',
        'score': 0.95,
        'model': 'test_model',
        'model_type': 'ml',
        'src_ip': '192.0.2.1',
        'dst_ip': '198.51.100.2',
        'src_port': 12345,
        'dst_port': 80,
        'protocol': 'TCP',
        'flow_duration': 12.34,
        'total_packets': 8,
        'total_bytes': 1024
    }

    if socketio:
        socketio.emit('prediction', sample, broadcast=True)
        logger.info('Emitted synthetic prediction for testing')
        return jsonify({'status': 'emitted', 'sample': sample})
    else:
        return jsonify({'error': 'Socket.IO not initialized'}), 500

@socketio.on('connect')
def handle_connect():
    """Handle WebSocket connection."""
    logger.info(f"Client connected: {request.sid}")
    print(f"[Socket.IO] Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to Real-Time IDS', 'status': 'connected'})
    data_source = realtime_ids.traffic_capture.get_data_source_type() if realtime_ids else "unknown"
    emit('status', {
        'message': 'Connected',
        'ids_running': realtime_ids.running if realtime_ids else False,
        'data_source': data_source,
        'active_flows': realtime_ids.traffic_capture.get_flow_count() if realtime_ids else 0,
        'timestamp': time.time()
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle WebSocket disconnection."""
    logger.info(f"Client disconnected: {request.sid}")
    print(f"[Socket.IO] Client disconnected: {request.sid}")


@socketio.on('start_monitoring')
def handle_start_monitoring():
    """Start real-time monitoring."""
    if realtime_ids and not realtime_ids.running:
        realtime_ids.start()
        data_source = realtime_ids.traffic_capture.get_data_source_type()
        emit('status', {
            'message': 'Monitoring started',
            'ids_running': True,
            'data_source': data_source,
            'active_flows': realtime_ids.traffic_capture.get_flow_count(),
            'timestamp': time.time()
        })
        heartbeat_payload = {
            'message': 'Monitoring started',
            'ids_running': True,
            'data_source': data_source,
            'active_flows': realtime_ids.traffic_capture.get_flow_count(),
            'timestamp': time.time(),
            'heartbeat': True
        }
        emit('heartbeat', heartbeat_payload)
        payload = {
            'label': 'normal',
            'anomaly_type': 'Monitoring Started',
            'score': 0.0,
            'model_type': 'system',
            'complexity': 0.0,
            'timestamp': time.time(),
            'src_ip': '127.0.0.1',
            'dst_ip': '127.0.0.1',
            'src_port': 0,
            'dst_port': 0,
            'protocol': 'SYSTEM',
            'flow_duration': 0.0,
            'total_packets': 0,
            'total_bytes': 0,
            'data_source': data_source
        }
        emit('prediction', payload)
        logger.info('Sent start_monitoring prediction event to client')
    elif realtime_ids and realtime_ids.running:
        data_source = realtime_ids.traffic_capture.get_data_source_type()
        emit('status', {
            'message': 'Monitoring already running',
            'ids_running': True,
            'data_source': data_source,
            'active_flows': realtime_ids.traffic_capture.get_flow_count(),
            'timestamp': time.time()
        })
        payload = {
            'label': 'normal',
            'anomaly_type': 'Monitoring already running',
            'score': 0.0,
            'model_type': 'system',
            'complexity': 0.0,
            'timestamp': time.time(),
            'src_ip': '127.0.0.1',
            'dst_ip': '127.0.0.1',
            'src_port': 0,
            'dst_port': 0,
            'protocol': 'SYSTEM',
            'flow_duration': 0.0,
            'total_packets': 0,
            'total_bytes': 0,
            'data_source': data_source
        }
        emit('prediction', payload)
        logger.info('Sent already-running prediction event to client')
    else:
        emit('status', {'message': 'IDS not initialized', 'ids_running': False, 'data_source': 'unknown', 'active_flows': 0, 'timestamp': time.time()})


@socketio.on('stop_monitoring')
def handle_stop_monitoring():
    """Stop real-time monitoring."""
    if realtime_ids and realtime_ids.running:
        realtime_ids.stop()
        data_source = realtime_ids.traffic_capture.get_data_source_type()
        emit('status', {
            'message': 'Monitoring stopped',
            'ids_running': False,
            'data_source': data_source,
            'active_flows': realtime_ids.traffic_capture.get_flow_count(),
            'timestamp': time.time()
        })
        heartbeat_payload = {
            'message': 'Monitoring stopped',
            'ids_running': False,
            'data_source': data_source,
            'active_flows': realtime_ids.traffic_capture.get_flow_count(),
            'timestamp': time.time(),
            'heartbeat': True
        }
        emit('heartbeat', heartbeat_payload)
        payload = {
            'label': 'normal',
            'anomaly_type': 'Monitoring Stopped',
            'score': 0.0,
            'model_type': 'system',
            'complexity': 0.0,
            'timestamp': time.time(),
            'src_ip': '127.0.0.1',
            'dst_ip': '127.0.0.1',
            'src_port': 0,
            'dst_port': 0,
            'protocol': 'SYSTEM',
            'flow_duration': 0.0,
            'total_packets': 0,
            'total_bytes': 0,
            'data_source': data_source
        }
        emit('prediction', payload)
        logger.info('Sent stop_monitoring prediction event to client')
    else:
        emit('status', {'message': 'Monitoring not running', 'ids_running': False, 'data_source': realtime_ids.traffic_capture.get_data_source_type() if realtime_ids else 'unknown', 'active_flows': realtime_ids.traffic_capture.get_flow_count() if realtime_ids else 0, 'timestamp': time.time()})


def initialize_ids(ml_model_path: str, dl_model_path: str, complexity_threshold: float = 50.0, interface: Optional[str] = None):
    """
    Initialize the real-time IDS system with adaptive predictor.
    
    Args:
        ml_model_path: Path to ML model
        dl_model_path: Path to DL model
        complexity_threshold: Threshold for model selection (> threshold uses DL)
        interface: Network interface for capture
    """
    global realtime_ids
    
    try:
        realtime_ids = RealtimeIDS(ml_model_path, dl_model_path, complexity_threshold, interface)
        logger.info("Real-time IDS initialized successfully with adaptive predictor")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize IDS: {e}")
        return False


def main():
    """Main function to run the Flask API server."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Real-Time Intrusion Detection System API')
    parser.add_argument('--ml-model', type=str, default='models/ml_best.pkl',
                       help='Path to ML model file')
    parser.add_argument('--dl-model', type=str, default='models/dl_lstm.h5',
                       help='Path to DL model file')
    parser.add_argument('--complexity-threshold', type=float, default=50.0,
                       help='Complexity threshold for model selection (> threshold uses DL)')
    parser.add_argument('--interface', type=str, default=None,
                       help='Network interface for capture (None for auto-detect)')
    parser.add_argument('--port', type=int, default=5000,
                       help='Port to run the server on')
    parser.add_argument('--host', type=str, default='0.0.0.0',
                       help='Host to bind to')
    parser.add_argument('--autostart', action='store_true',
                       help='Automatically start IDS monitoring on server launch')
    
    args = parser.parse_args()
    
    if not FLASK_AVAILABLE:
        print("Flask not available. Install with: pip install flask flask-cors flask-socketio")
        return 1
    
    # Initialize IDS with adaptive predictor
    if not initialize_ids(args.ml_model, args.dl_model, args.complexity_threshold, args.interface):
        print("Failed to initialize IDS")
        return 1

    if args.autostart:
        realtime_ids.start()
        print("Auto-start enabled: IDS monitoring started")
    else:
        print("Auto-start disabled: IDS monitoring is stopped until Start Detection is requested")

    print(f"Starting Real-Time IDS API server on {args.host}:{args.port}")
    print(f"ML Model: {args.ml_model}")
    print(f"DL Model: {args.dl_model}")
    print(f"Complexity Threshold: {args.complexity_threshold}")
    print(f"Interface: {args.interface or 'auto-detect'}")
    print("\nEndpoints:")
    print(f"  - http://{args.host}:{args.port}/")
    print(f"  - http://{args.host}:{args.port}/health")
    print(f"  - http://{args.host}:{args.port}/predict (POST)")
    print(f"  - http://{args.host}:{args.port}/stats")
    print(f"  - http://{args.host}:{args.port}/attacks")
    print("\nWebSocket:")
    print(f"  - ws://{args.host}:{args.port}/socket.io/")
    print("\nPress Ctrl+C to stop")
    
    try:
        socketio.run(app, host=args.host, port=args.port, debug=False)
    except KeyboardInterrupt:
        print("\nStopping server...")
        if realtime_ids:
            realtime_ids.stop()
        print("Server stopped")
    
    return 0


if __name__ == '__main__':
    exit(main())

