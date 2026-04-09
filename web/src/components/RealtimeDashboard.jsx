import { useEffect, useRef, useState } from 'react';
import io from 'socket.io-client';

const RealTimeDashboard = () => {
  const [events, setEvents] = useState([]);
  const [status, setStatus] = useState('disconnected');
  const [isDetecting, setIsDetecting] = useState(false);
  const [dataSource, setDataSource] = useState('unknown');
  const [activeFlows, setActiveFlows] = useState(0);
  const [lastStatusTime, setLastStatusTime] = useState(null);
  const [statusMessage, setStatusMessage] = useState('');
  const [monitorDuration, setMonitorDuration] = useState(0);
  const [heartbeatCount, setHeartbeatCount] = useState(0);
  const [lastEventType, setLastEventType] = useState('none');
  const socketRef = useRef(null);
  const monitorIntervalRef = useRef(null);

  useEffect(() => {
    // Connect to Flask-SocketIO WebSocket for real-time IDS updates
    const socket = io('http://localhost:5001');
    socketRef.current = socket;

    socket.on('connect', () => {
      setStatus('connected');
      console.log('Connected to IDS server');
    });

    socket.on('prediction', (data) => {
      console.log('Received prediction:', data);
      if (data.data_source) {
        setDataSource(data.data_source);
      }
      if (data.message) {
        setStatusMessage(data.message);
      }
      if (data.data_source) {
        setDataSource(data.data_source);
      }
      if (data.message) {
        setStatusMessage(data.message);
      }
      setLastEventType('prediction');
      setEvents((prev) => {
        const next = [data, ...prev];
        return next.slice(0, 50);
      });
    });

    socket.on('status', (data) => {
      console.log('Status update:', data);
      if (data.data_source) {
        setDataSource(data.data_source);
      }
      if (typeof data.active_flows === 'number') {
        setActiveFlows(data.active_flows);
      }
      const timestamp = data.timestamp || Date.now() / 1000;
      setLastStatusTime(timestamp);
      if (data.message) {
        setStatusMessage(data.message);
      }
      if (typeof data.ids_running === 'boolean') {
        setIsDetecting(data.ids_running);
      } else if (data.message && data.message.includes('Monitoring started')) {
        setIsDetecting(true);
      } else if (data.message && data.message.includes('Monitoring stopped')) {
        setIsDetecting(false);
      } else if (data.message && data.message.includes('already running')) {
        setIsDetecting(true);
      }
      setLastEventType('status');
    });

    socket.on('heartbeat', (data) => {
      console.log('Heartbeat update:', data);
      if (data.data_source) {
        setDataSource(data.data_source);
      }
      if (typeof data.active_flows === 'number') {
        setActiveFlows(data.active_flows);
      }
      if (data.timestamp) {
        setLastStatusTime(data.timestamp);
      }
      if (data.message) {
        setStatusMessage(data.message);
      }
      if (typeof data.ids_running === 'boolean') {
        setIsDetecting(data.ids_running);
      }
      setLastEventType('heartbeat');
      const heartbeatEvent = {
        label: 'normal',
        anomaly_type: data.message || 'Live heartbeat',
        score: 0.0,
        model_type: 'system',
        complexity: 0.0,
        timestamp: data.timestamp || Date.now() / 1000,
        src_ip: data.data_source === 'real' ? 'real-traffic' : 'synthetic-test',
        dst_ip: 'monitor',
        src_port: 0,
        dst_port: 0,
        protocol: 'SYSTEM',
        flow_duration: 0.0,
        total_packets: 0,
        total_bytes: 0,
        data_source: data.data_source || dataSource,
        heartbeat: true
      };
      setHeartbeatCount((count) => count + 1);
      setEvents((prev) => {
        const next = [heartbeatEvent, ...prev];
        return next.slice(0, 50);
      });
    });

    socket.on('disconnect', () => {
      setStatus('disconnected');
      setIsDetecting(false);
    });

    socket.on('connect_error', (err) => {
      console.error('WebSocket connect_error:', err);
      setStatus('error');
      setIsDetecting(false);
    });

    return () => {
      if (monitorIntervalRef.current) {
        clearInterval(monitorIntervalRef.current);
      }
      socket.disconnect();
    };
  }, []);

  const handleStart = async () => {
    try {
      if (socketRef.current) {
        console.log('Emitting start_monitoring');
        socketRef.current.emit('start_monitoring');
        setIsDetecting(true);
        setMonitorDuration(0);
        if (monitorIntervalRef.current) {
          clearInterval(monitorIntervalRef.current);
        }
        monitorIntervalRef.current = setInterval(() => {
          setMonitorDuration((value) => value + 1);
        }, 1000);
      } else {
        console.error('Socket not initialized');
      }
    } catch (err) {
      console.error('Failed to start realtime IDS', err);
    }
  };

  const handleStop = async () => {
    try {
      if (socketRef.current) {
        console.log('Emitting stop_monitoring');
        socketRef.current.emit('stop_monitoring');
        setIsDetecting(false);
        if (monitorIntervalRef.current) {
          clearInterval(monitorIntervalRef.current);
          monitorIntervalRef.current = null;
        }
      } else {
        console.error('Socket not initialized');
      }
    } catch (err) {
      console.error('Failed to stop realtime IDS', err);
    }
  };

  return (
    <section className="py-20 bg-gradient-to-br from-indigo-50 to-blue-50">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900">
              Real-Time IDS Dashboard
            </h2>
            <p className="mt-2 text-gray-600">
              Live stream of network flows and anomaly predictions from the backend (real or synthetic data).
            </p>
          </div>
          <div className="flex items-center space-x-3">
            <span
              className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                status === 'connected'
                  ? 'bg-green-100 text-green-800'
                  : status === 'error'
                  ? 'bg-red-100 text-red-800'
                  : 'bg-gray-100 text-gray-800'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full mr-2 ${
                  status === 'connected'
                    ? 'bg-green-500'
                    : status === 'error'
                    ? 'bg-red-500'
                    : 'bg-gray-400'
                }`}
              />
              {status === 'connected' ? 'WebSocket Connected' : status === 'error' ? 'Error' : 'Disconnected'}
            </span>
            <span
              className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                dataSource === 'real'
                  ? 'bg-green-100 text-green-800'
                  : dataSource === 'synthetic'
                  ? 'bg-yellow-100 text-yellow-800'
                  : 'bg-gray-100 text-gray-600'
              }`}
            >
              <span
                className={`w-2 h-2 rounded-full mr-2 ${
                  dataSource === 'real'
                    ? 'bg-green-500'
                    : dataSource === 'synthetic'
                    ? 'bg-yellow-500'
                    : 'bg-gray-400'
                }`}
              />
              {dataSource === 'real' ? 'Real Data' : dataSource === 'synthetic' ? 'Synthetic Data' : 'Unknown Source'}
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mb-6">
          <div className="bg-white rounded-xl shadow p-4">
            <div className="text-xs uppercase tracking-wide text-gray-500">Last update</div>
            <div className="mt-2 text-lg font-semibold text-gray-900">
              {lastStatusTime ? new Date(lastStatusTime * 1000).toLocaleTimeString() : 'No status received yet'}
            </div>
            <div className="mt-1 text-xs text-gray-600">{statusMessage || 'No status yet'}</div>
          </div>
          <div className="bg-white rounded-xl shadow p-4">
            <div className="text-xs uppercase tracking-wide text-gray-500">Active flow count</div>
            <div className="mt-2 text-lg font-semibold text-gray-900">{activeFlows}</div>
            <div className="mt-1 text-xs text-gray-600">Flows currently captured by the IDS</div>
          </div>
          <div className="bg-white rounded-xl shadow p-4">
            <div className="text-xs uppercase tracking-wide text-gray-500">Data source</div>
            <div className="mt-2 text-lg font-semibold text-gray-900">{dataSource === 'real' ? 'Real Data' : dataSource === 'synthetic' ? 'Synthetic Data' : 'Unknown'}</div>
            <div className="mt-1 text-xs text-gray-600">Source of the traffic being analyzed</div>
          </div>
          <div className="bg-white rounded-xl shadow p-4">
            <div className="text-xs uppercase tracking-wide text-gray-500">Heartbeat count</div>
            <div className="mt-2 text-lg font-semibold text-gray-900">{heartbeatCount}</div>
            <div className="mt-1 text-xs text-gray-600">Backend heartbeat events received</div>
            <div className="mt-4 text-xs uppercase tracking-wide text-gray-500">Last backend event</div>
            <div className="mt-2 text-base font-semibold text-gray-900">{lastEventType}</div>
          </div>
        </div>
        <div className="flex items-center space-x-3 mb-6">
          <button
            type="button"
            onClick={handleStart}
            disabled={isDetecting || status !== 'connected'}
            className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium focus:ring-2 focus:ring-offset-2 transition-colors ${
              isDetecting || status !== 'connected'
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-green-600 text-white hover:bg-green-700 focus:ring-green-500'
            }`}
          >
            Start Detection
          </button>
          <button
            type="button"
            onClick={handleStop}
            disabled={!isDetecting}
            className={`inline-flex items-center px-4 py-2 rounded-lg text-sm font-medium focus:ring-2 focus:ring-offset-2 transition-colors ${
              !isDetecting
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500'
            }`}
          >
            Stop Detection
          </button>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6 max-h-[480px] overflow-y-auto">
          {events.length === 0 ? (
            <p className="text-gray-500 text-sm">
              No events yet. Click &quot;Start Detection&quot; and keep this page open to view real-time updates.
            </p>
          ) : (
            <div className="space-y-3">
              {events.map((e, idx) => {
                const label = e?.label ?? 'unknown';
                const score = e?.score;
                const attackType = e?.anomaly_type;
                const modelType = e?.model_type;
                const complexity = e?.complexity;
                const isAnomaly = label === 'anomaly';

                return (
                  <div
                    key={idx}
                    className={`border rounded-lg p-4 flex items-start justify-between ${
                      isAnomaly ? 'border-red-200 bg-red-50' : 'border-green-200 bg-green-50'
                    }`}
                  >
                    <div>
                      <div className="flex items-center space-x-2">
                        <span
                          className={`px-2 py-1 text-xs font-semibold rounded-full uppercase ${
                            isAnomaly
                              ? 'bg-red-100 text-red-800'
                              : 'bg-green-100 text-green-800'
                          }`}
                        >
                          {label}
                        </span>
                        {typeof score === 'number' && (
                          <span className="text-xs text-gray-700">
                            confidence: {(score * 100).toFixed(1)}%
                          </span>
                        )}
                        {modelType && (
                          <span className="text-xs text-blue-600 bg-blue-50 px-2 py-1 rounded">
                            {modelType.toUpperCase()}
                          </span>
                        )}
                      </div>
                      {attackType && (
                        <div className="mt-2 text-xs text-gray-700">
                          <span className="font-medium">type:</span>{' '}
                          {attackType}
                        </div>
                      )}
                      {(e.src_ip || e.dst_ip) && (
                        <div className="mt-1 text-xs text-gray-600">
                          {e.src_ip || 'unknown'} → {e.dst_ip || 'unknown'}
                          {e.src_port !== undefined && e.dst_port !== undefined && (
                            <span> ({e.src_port}:{e.dst_port})</span>
                          )}
                        </div>
                      )}
                      {(e.total_packets || e.total_bytes) && (
                        <div className="mt-1 text-xs text-gray-600">
                          {e.total_packets !== undefined && <span>{e.total_packets} pkt</span>}
                          {e.total_bytes !== undefined && <span>{e.total_packets !== undefined ? ' · ' : ''}{e.total_bytes} bytes</span>}
                        </div>
                      )}
                      {complexity !== undefined && (
                        <div className="mt-1 text-xs text-gray-600">
                          <span className="font-medium">complexity:</span>{' '}
                          {complexity.toFixed(2)}
                        </div>
                      )}
                      {e.data_source && (
                        <div className="mt-1 text-xs text-purple-600 bg-purple-50 px-2 py-1 rounded inline-block">
                          {e.data_source.toUpperCase()} DATA
                        </div>
                      )}
                      {e.timestamp && (
                        <div className="mt-1 text-xs text-gray-500">
                          {new Date(e.timestamp * 1000).toLocaleTimeString()}
                        </div>
                      )}
                    </div>
                    <span className="text-[10px] text-gray-500 mt-1">
                      #{events.length - idx}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </section>
  );
};

export default RealTimeDashboard;

