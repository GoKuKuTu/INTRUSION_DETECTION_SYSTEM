import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Activity, 
  AlertTriangle, 
  Shield, 
  Wifi, 
  Play, 
  Square,
  TrendingUp,
  Clock,
  MapPin
} from 'lucide-react';
import io from 'socket.io-client';

const RealtimeDashboard = () => {
  const [isMonitoring, setIsMonitoring] = useState(false);
  const [predictions, setPredictions] = useState([]);
  const [stats, setStats] = useState({
    totalFlows: 0,
    normalFlows: 0,
    attackFlows: 0,
    activeFlows: 0
  });
  const [recentAttacks, setRecentAttacks] = useState([]);
  const [socket, setSocket] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const predictionsRef = useRef([]);
  const maxPredictions = 100; // Keep last 100 predictions

  // IMPORTANT: Backend is running on port 5001 in this session
  // Point client to the realtime server started on 5001
  const API_BASE = 'http://localhost:5001';
  
  // Debug: Log the API base URL
  console.log('🔧 API_BASE configured as:', API_BASE);
  console.log('🔧 Connecting to backend on port 5000');

  useEffect(() => {
    // Initialize Socket.IO connection
    console.log('🔌 Initializing Socket.IO connection to:', API_BASE);
    const newSocket = io(API_BASE, {
      // Use polling transport by default to avoid websocket handshake
      // errors when the Python backend isn't running an async server
      // like eventlet/gevent which provides websocket support.
      transports: ['polling'],
      reconnection: true,
      reconnectionDelay: 1000,
      reconnectionAttempts: 10,
      timeout: 20000,
      forceNew: false, // Don't force new connection on re-render
      autoConnect: true
    });

    // Connection event handlers
    newSocket.on('connect', () => {
      console.log('✅ Socket.IO Connected! ID:', newSocket.id);
      setConnectionStatus('connected');
      fetchStats(); // Fetch stats after connection
    });

    newSocket.on('disconnect', (reason) => {
      console.log('❌ Socket.IO Disconnected. Reason:', reason);
      setConnectionStatus('disconnected');
    });

    newSocket.on('connect_error', (error) => {
      console.error('❌ Socket.IO Connection Error:', error);
      console.error('Error details:', error.message, error.type);
      setConnectionStatus('disconnected');
    });

    newSocket.on('connected', (data) => {
      console.log('📨 Server connected message:', data);
      setConnectionStatus('connected');
    });

    newSocket.on('prediction', (data) => {
      handlePrediction(data);
    });

    newSocket.on('status', (data) => {
      console.log('Status:', data);
    });

    // Set socket
    setSocket(newSocket);

    // Cleanup on unmount only
    return () => {
      console.log('🧹 Component unmounting - cleaning up Socket.IO');
      if (newSocket && newSocket.connected) {
        newSocket.disconnect();
      }
      newSocket.removeAllListeners();
      newSocket.close();
    };
  }, []); // Empty deps - only run once on mount

  useEffect(() => {
    // Update stats periodically
    const interval = setInterval(() => {
      if (isMonitoring) {
        fetchStats();
      }
    }, 5000); // Every 5 seconds

    return () => clearInterval(interval);
  }, [isMonitoring]);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(prev => ({
          ...prev,
          activeFlows: data.active_flows || 0
        }));
      }
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const handlePrediction = (prediction) => {
    const timestamp = new Date().toLocaleTimeString();
    const predictionWithTime = {
      ...prediction,
      id: Date.now() + Math.random(),
      timestamp
    };

    predictionsRef.current = [predictionWithTime, ...predictionsRef.current].slice(0, maxPredictions);
    setPredictions(predictionsRef.current);

    // Update stats
    setStats(prev => {
      const newStats = { ...prev };
      newStats.totalFlows += 1;
      if (prediction.label === 'anomaly') {
        newStats.attackFlows += 1;
        setRecentAttacks(prev => [predictionWithTime, ...prev].slice(0, 10));
      } else {
        newStats.normalFlows += 1;
      }
      return newStats;
    });
  };

  const startMonitoring = () => {
    if (socket) {
      socket.emit('start_monitoring');
      setIsMonitoring(true);
    }
  };

  const stopMonitoring = () => {
    if (socket) {
      socket.emit('stop_monitoring');
      setIsMonitoring(false);
    }
  };

  const getStatusColor = () => {
    if (connectionStatus === 'connected') {
      return isMonitoring ? 'text-green-500' : 'text-yellow-500';
    }
    return 'text-red-500';
  };

  const getStatusText = () => {
    if (connectionStatus === 'disconnected') return 'Disconnected';
    if (connectionStatus === 'connected') return isMonitoring ? 'Monitoring Active' : 'Connected - Ready';
    return 'Connecting...';
  };

  return (
    <section id="realtime" className="py-20 bg-gradient-to-br from-gray-50 to-blue-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-12"
        >
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
            Real-Time Intrusion Detection
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Live network traffic monitoring and anomaly detection
          </p>
        </motion.div>

        {/* Control Panel */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="bg-white rounded-xl shadow-lg p-6 mb-8"
        >
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center space-x-4">
              <div className={`flex items-center space-x-2 ${getStatusColor()}`}>
                <Activity className="w-5 h-5" />
                <span className="font-medium">{getStatusText()}</span>
              </div>
              <div className="text-sm text-gray-600">
                Active Flows: <span className="font-semibold">{stats.activeFlows}</span>
              </div>
            </div>
            <div className="flex space-x-3">
              {!isMonitoring ? (
                <button
                  onClick={startMonitoring}
                  disabled={connectionStatus !== 'connected'}
                  className="flex items-center space-x-2 bg-green-600 text-white px-6 py-2 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Play className="w-4 h-4" />
                  <span>Start Monitoring</span>
                </button>
              ) : (
                <button
                  onClick={stopMonitoring}
                  className="flex items-center space-x-2 bg-red-600 text-white px-6 py-2 rounded-lg hover:bg-red-700 transition-colors"
                >
                  <Square className="w-4 h-4" />
                  <span>Stop Monitoring</span>
                </button>
              )}
            </div>
          </div>
        </motion.div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
            className="bg-white rounded-xl shadow-lg p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Total Flows</p>
                <p className="text-3xl font-bold text-gray-900">{stats.totalFlows}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-blue-600" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
            className="bg-white rounded-xl shadow-lg p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Normal Flows</p>
                <p className="text-3xl font-bold text-green-600">{stats.normalFlows}</p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                <Shield className="w-6 h-6 text-green-600" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4 }}
            className="bg-white rounded-xl shadow-lg p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Attack Flows</p>
                <p className="text-3xl font-bold text-red-600">{stats.attackFlows}</p>
              </div>
              <div className="w-12 h-12 bg-red-100 rounded-lg flex items-center justify-center">
                <AlertTriangle className="w-6 h-6 text-red-600" />
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5 }}
            className="bg-white rounded-xl shadow-lg p-6"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 mb-1">Active Flows</p>
                <p className="text-3xl font-bold text-blue-600">{stats.activeFlows}</p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                <Wifi className="w-6 h-6 text-purple-600" />
              </div>
            </div>
          </motion.div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Recent Attacks */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.6 }}
            className="bg-white rounded-xl shadow-lg p-6"
          >
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              <span>Recent Attacks</span>
            </h3>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              <AnimatePresence>
                {recentAttacks.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No attacks detected yet</p>
                ) : (
                  recentAttacks.map((attack) => (
                    <motion.div
                      key={attack.id}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: 20 }}
                      className="bg-red-50 border-l-4 border-red-500 p-4 rounded-lg"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <p className="font-semibold text-red-900">{attack.anomaly_type || 'Unknown Attack'}</p>
                          <p className="text-sm text-red-700">
                            {attack.src_ip} → {attack.dst_ip}
                          </p>
                        </div>
                        <span className="text-xs text-gray-500">{attack.timestamp}</span>
                      </div>
                      <div className="flex items-center space-x-4 text-sm text-gray-600">
                        <span>Port: {attack.dst_port}</span>
                        <span>Confidence: {(attack.score * 100).toFixed(1)}%</span>
                      </div>
                    </motion.div>
                  ))
                )}
              </AnimatePresence>
            </div>
          </motion.div>

          {/* Live Predictions Stream */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.7 }}
            className="bg-white rounded-xl shadow-lg p-6"
          >
            <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center space-x-2">
              <Activity className="w-5 h-5 text-blue-600" />
              <span>Live Predictions</span>
            </h3>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              <AnimatePresence>
                {predictions.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">Waiting for predictions...</p>
                ) : (
                  predictions.slice(0, 20).map((prediction) => (
                    <motion.div
                      key={prediction.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      className={`p-3 rounded-lg border-l-4 ${
                        prediction.label === 'anomaly'
                          ? 'bg-red-50 border-red-500'
                          : 'bg-green-50 border-green-500'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className={`font-semibold ${
                          prediction.label === 'anomaly' ? 'text-red-900' : 'text-green-900'
                        }`}>
                          {prediction.label === 'anomaly' ? '⚠️ Attack' : '✓ Normal'}
                        </span>
                        <span className="text-xs text-gray-500">{prediction.timestamp}</span>
                      </div>
                      <div className="text-sm text-gray-600">
                        <div className="flex items-center space-x-4">
                          <span className="flex items-center space-x-1">
                            <MapPin className="w-3 h-3" />
                            <span>{prediction.src_ip}:{prediction.src_port}</span>
                          </span>
                          <span>→</span>
                          <span>{prediction.dst_ip}:{prediction.dst_port}</span>
                        </div>
                        {prediction.anomaly_type && (
                          <p className="text-red-700 mt-1">Type: {prediction.anomaly_type}</p>
                        )}
                        <p className="text-gray-500 mt-1">
                          Confidence: {(prediction.score * 100).toFixed(1)}%
                        </p>
                      </div>
                    </motion.div>
                  ))
                )}
              </AnimatePresence>
            </div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};

export default RealtimeDashboard;

