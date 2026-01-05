const express = require('express');
const cors = require('cors');
const app = express();
const port = 8000;

// Enable CORS for frontend
app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', message: 'API is running' });
});

// Root endpoint
app.get('/', (req, res) => {
  res.json({ 
    message: 'Network Anomaly Detection API', 
    version: '1.0.0',
    docs: '/docs'
  });
});

// Prediction endpoint
app.post('/predict', (req, res) => {
  try {
    const { features } = req.body;
    
    if (!features || !Array.isArray(features) || features.length < 5) {
      return res.status(400).json({ error: 'At least 5 features required' });
    }
    
    // Extract features (flow_duration, packet_count, byte_count, protocol, port)
    const [flow_duration, packet_count, byte_count, protocol, port] = features;
    
    // Determine anomaly type based on feature patterns
    let anomaly_type = 'normal';
    let confidence = 0.0;
    
    // DDoS Attack - High packet count and byte count
    if (packet_count > 1000 && byte_count > 50000) {
      anomaly_type = 'DDoS Attack';
      confidence = Math.min((packet_count + byte_count/100) / 2000, 1.0);
    }
    // Port Scan - High flow duration with low packet count
    else if (flow_duration > 500 && packet_count < 10) {
      anomaly_type = 'Port Scan';
      confidence = Math.min(flow_duration / 1000, 1.0);
    }
    // Brute Force - High packet count with low byte count
    else if (packet_count > 500 && byte_count < 1000) {
      anomaly_type = 'Brute Force Attack';
      confidence = Math.min(packet_count / 1000, 1.0);
    }
    // Suspicious Protocol - Unusual protocol usage
    else if (![1, 6, 17].includes(protocol)) { // Not ICMP, TCP, or UDP
      anomaly_type = 'Suspicious Protocol';
      confidence = 0.8;
    }
    // Suspicious Port - Well-known attack ports
    else if ([22, 23, 135, 139, 445, 1433, 3389].includes(port)) { // SSH, Telnet, RPC, SMB, SQL, RDP
      anomaly_type = 'Suspicious Port Access';
      confidence = 0.7;
    }
    // High Traffic - Very high byte count
    else if (byte_count > 100000) {
      anomaly_type = 'High Traffic Anomaly';
      confidence = Math.min(byte_count / 200000, 1.0);
    }
    // Long Duration - Suspiciously long flow
    else if (flow_duration > 1000) {
      anomaly_type = 'Long Duration Flow';
      confidence = Math.min(flow_duration / 2000, 1.0);
    }
    // Normal traffic
    else {
      anomaly_type = 'normal';
      confidence = 0.1; // Low confidence for normal traffic
    }
    
    res.json({
      label: anomaly_type !== 'normal' ? 'anomaly' : 'normal',
      anomaly_type: anomaly_type,
      score: confidence,
      model: 'enhanced_test_model',
      model_type: 'ml',
      details: {
        flow_duration: flow_duration,
        packet_count: packet_count,
        byte_count: byte_count,
        protocol: protocol,
        port: port
      }
    });
    
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// Start server
app.listen(port, '0.0.0.0', () => {
  console.log('===============================================');
  console.log('  NETWORK ANOMALY DETECTION API SERVER');
  console.log('===============================================');
  console.log(`Server running on http://localhost:${port}`);
  console.log(`Health check: http://localhost:${port}/health`);
  console.log('===============================================');
  console.log('Keep this window open while using your frontend!');
  console.log('Press Ctrl+C to stop the server');
});
