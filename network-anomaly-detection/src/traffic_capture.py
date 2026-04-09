#!/usr/bin/env python3
"""
Real-Time Network Traffic Capture Module

This module captures live network traffic using Scapy and extracts flow-based
features compatible with the trained ML models.

Features:
- Live packet capture from network interface
- Flow-based feature extraction (CICFlowMeter compatible)
- Real-time packet processing
- Thread-safe queue for packet handling

Usage:
    from traffic_capture import TrafficCapture
    
    capture = TrafficCapture(interface='eth0')
    capture.start()
    packet = capture.get_packet()
"""

import threading
import queue
import time
import logging
from collections import defaultdict
from typing import Dict, Optional, Tuple, List
from datetime import datetime
import socket
import struct
import random

try:
    from scapy.all import sniff, IP, TCP, UDP, ICMP, Raw, get_if_list
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False
    logging.warning("Scapy not available. Install with: pip install scapy")

logger = logging.getLogger(__name__)


class Flow:
    """
    Represents a network flow with bidirectional traffic.
    """
    
    def __init__(self, src_ip: str, dst_ip: str, src_port: int, dst_port: int, protocol: str):
        self.src_ip = src_ip
        self.dst_ip = dst_ip
        self.src_port = src_port
        self.dst_port = dst_port
        self.protocol = protocol
        
        # Forward direction (src -> dst)
        self.fwd_packets = 0
        self.fwd_bytes = 0
        self.fwd_timestamps = []
        
        # Backward direction (dst -> src)
        self.bwd_packets = 0
        self.bwd_bytes = 0
        self.bwd_timestamps = []
        
        # TCP flags
        self.fin_count = 0
        self.syn_count = 0
        self.rst_count = 0
        self.psh_count = 0
        self.ack_count = 0
        self.urg_count = 0
        
        # Flow metadata
        self.start_time = time.time()
        self.last_seen = time.time()
        self.is_active = True
        
    def add_packet(self, packet_bytes: int, direction: str, timestamp: float, flags: Dict[str, int] = None):
        """Add a packet to the flow."""
        self.last_seen = timestamp
        
        if direction == 'forward':
            self.fwd_packets += 1
            self.fwd_bytes += packet_bytes
            self.fwd_timestamps.append(timestamp)
        else:
            self.bwd_packets += 1
            self.bwd_bytes += packet_bytes
            self.bwd_timestamps.append(timestamp)
        
        # Update TCP flags
        if flags:
            self.fin_count += flags.get('FIN', 0)
            self.syn_count += flags.get('SYN', 0)
            self.rst_count += flags.get('RST', 0)
            self.psh_count += flags.get('PSH', 0)
            self.ack_count += flags.get('ACK', 0)
            self.urg_count += flags.get('URG', 0)
    
    def get_duration(self) -> float:
        """Get flow duration in milliseconds."""
        if not self.fwd_timestamps and not self.bwd_timestamps:
            return 0.0
        all_timestamps = self.fwd_timestamps + self.bwd_timestamps
        return (max(all_timestamps) - min(all_timestamps)) * 1000  # Convert to ms
    
    def get_iat_stats(self) -> Tuple[float, float]:
        """Calculate inter-arrival time statistics."""
        all_timestamps = sorted(self.fwd_timestamps + self.bwd_timestamps)
        if len(all_timestamps) < 2:
            return 0.0, 0.0
        
        iats = []
        for i in range(1, len(all_timestamps)):
            iat = (all_timestamps[i] - all_timestamps[i-1]) * 1000  # Convert to ms
            iats.append(iat)
        
        if not iats:
            return 0.0, 0.0
        
        mean = sum(iats) / len(iats)
        variance = sum((x - mean) ** 2 for x in iats) / len(iats)
        std = variance ** 0.5
        
        return mean, std
    
    def get_packet_length_stats(self) -> Tuple[float, float]:
        """Calculate packet length statistics."""
        # Estimate packet sizes (simplified - in real implementation, track actual sizes)
        total_packets = self.fwd_packets + self.bwd_packets
        total_bytes = self.fwd_bytes + self.bwd_bytes
        
        if total_packets == 0:
            return 0.0, 0.0
        
        mean = total_bytes / total_packets
        
        # Estimate std (simplified)
        std = mean * 0.2  # Assume 20% variation
        
        return mean, std


class TrafficCapture:
    """
    Real-time network traffic capture and flow extraction.
    """
    
    def __init__(self, interface: Optional[str] = None, timeout: float = 30.0):
        """
        Initialize traffic capture.
        
        Args:
            interface: Network interface name (None for auto-detect)
            timeout: Flow timeout in seconds (flows older than this are expired)
        """
        if not SCAPY_AVAILABLE:
            raise ImportError("Scapy is required. Install with: pip install scapy")
        
        self.interface = interface or self._detect_interface()
        self.timeout = timeout
        self.packet_queue = queue.Queue()
        self.flows: Dict[Tuple[str, str, int, int, str], Flow] = {}
        self.expired_flows = queue.Queue()
        self.running = False
        self.capture_thread = None
        self.flow_cleanup_thread = None
        self.using_mock_data = False  # Track whether we're using mock data
        
        logger.info(f"Initialized TrafficCapture on interface: {self.interface}")
    
    def _detect_interface(self) -> str:
        """Auto-detect the best network interface."""
        try:
            interfaces = get_if_list()
            # Prefer common interface names
            preferred = ['eth0', 'en0', 'wlan0', 'Wi-Fi', 'Ethernet']
            for pref in preferred:
                if pref in interfaces:
                    return pref
            return interfaces[0] if interfaces else 'any'
        except:
            return 'any'
    
    def _packet_handler(self, packet):
        """Handle captured packets."""
        try:
            if not packet.haslayer(IP):
                return
            
            ip_layer = packet[IP]
            src_ip = ip_layer.src
            dst_ip = ip_layer.dst
            protocol_num = ip_layer.proto
            
            # Map protocol number to name
            protocol_map = {1: 'ICMP', 6: 'TCP', 17: 'UDP'}
            protocol = protocol_map.get(protocol_num, 'UNKNOWN')
            
            # Extract port information
            src_port = 0
            dst_port = 0
            flags = {}
            
            if packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                src_port = tcp_layer.sport
                dst_port = tcp_layer.dport
                flags = {
                    'FIN': 1 if tcp_layer.flags & 0x01 else 0,
                    'SYN': 1 if tcp_layer.flags & 0x02 else 0,
                    'RST': 1 if tcp_layer.flags & 0x04 else 0,
                    'PSH': 1 if tcp_layer.flags & 0x08 else 0,
                    'ACK': 1 if tcp_layer.flags & 0x10 else 0,
                    'URG': 1 if tcp_layer.flags & 0x20 else 0,
                }
            elif packet.haslayer(UDP):
                udp_layer = packet[UDP]
                src_port = udp_layer.sport
                dst_port = udp_layer.dport
            elif packet.haslayer(ICMP):
                # ICMP doesn't have ports, use type/code
                src_port = 0
                dst_port = 0
            
            # Determine flow direction (use 5-tuple: src_ip, dst_ip, src_port, dst_port, protocol)
            # Normalize flow key (smaller IP first for bidirectional flows)
            if src_ip < dst_ip or (src_ip == dst_ip and src_port < dst_port):
                flow_key = (src_ip, dst_ip, src_port, dst_port, protocol)
                direction = 'forward'
            else:
                flow_key = (dst_ip, src_ip, dst_port, src_port, protocol)
                direction = 'backward'
            
            # Get or create flow
            if flow_key not in self.flows:
                if direction == 'forward':
                    self.flows[flow_key] = Flow(src_ip, dst_ip, src_port, dst_port, protocol)
                else:
                    self.flows[flow_key] = Flow(dst_ip, src_ip, dst_port, src_port, protocol)
            
            flow = self.flows[flow_key]
            
            # Calculate packet size
            packet_size = len(packet)
            timestamp = time.time()
            
            # Add packet to flow
            flow.add_packet(packet_size, direction, timestamp, flags)
            
            # Put flow in queue for processing (only when flow is complete or expired)
            # For real-time, we'll process flows periodically
            
        except Exception as e:
            logger.error(f"Error processing packet: {e}")
    
    def _capture_loop(self):
        """Main packet capture loop."""
        try:
            logger.info(f"Starting packet capture on {self.interface}")
            sniff(
                iface=self.interface,
                prn=self._packet_handler,
                stop_filter=lambda x: not self.running,
                store=False
            )
        except Exception as e:
            logger.error(f"Capture error: {e}")
            # If packet capture is unavailable (common on Windows without Npcap),
            # fall back to a mock generator so the realtime pipeline can be tested.
            self.running = True
            try:
                msg = str(e).lower()
            except:
                msg = ''

            if 'pcap' in msg or 'winpcap' in msg or 'npcap' in msg or 'sniff' in msg:
                logger.warning("Packet capture unavailable, starting mock traffic generator")
                self._start_mock_generator()
            else:
                # Unknown capture error - stop capture
                self.running = False
    
    def _cleanup_expired_flows(self):
        """Periodically clean up expired flows."""
        while self.running:
            try:
                current_time = time.time()
                expired_keys = []
                
                for flow_key, flow in self.flows.items():
                    if current_time - flow.last_seen > self.timeout:
                        expired_keys.append(flow_key)
                        self.expired_flows.put(flow)
                
                for key in expired_keys:
                    del self.flows[key]
                
                time.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Error in flow cleanup: {e}")
    
    def start(self):
        """Start capturing traffic."""
        if self.running:
            logger.warning("Capture already running")
            return
        
        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.flow_cleanup_thread = threading.Thread(target=self._cleanup_expired_flows, daemon=True)
        
        self.capture_thread.start()
        self.flow_cleanup_thread.start()
        # If capture failed quickly, ensure mock generator is started
        # (the _capture_loop will initialize mock if necessary)
        
        logger.info("Traffic capture started")
    
    def stop(self):
        """Stop capturing traffic."""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=2)
        if self.flow_cleanup_thread:
            self.flow_cleanup_thread.join(timeout=2)
        logger.info("Traffic capture stopped")
    
    def get_expired_flow(self, timeout: float = 1.0) -> Optional[Flow]:
        """Get an expired flow for processing."""
        try:
            return self.expired_flows.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_active_flows(self) -> List[Flow]:
        """Get all currently active flows."""
        return list(self.flows.values())
    
    def get_flow_count(self) -> int:
        """Get number of active flows."""
        return len(self.flows)
    
    def get_data_source_type(self) -> str:
        """Get the type of data source being used."""
        return "synthetic" if self.using_mock_data else "real"

    # --- Mock generator for environments without libpcap ---
    def _start_mock_generator(self):
        """Start a background thread that generates synthetic flows for testing."""
        if getattr(self, 'mocking', False):
            return
        self.mocking = True
        self.using_mock_data = True  # Set flag to indicate we're using mock data
        self.mock_thread = threading.Thread(target=self._mock_loop, daemon=True)
        self.mock_thread.start()
        logger.info("Mock traffic generator started")

    def _mock_loop(self):
        """Generate synthetic flows and push them to expired_flows periodically."""
        while self.running and getattr(self, 'mocking', False):
            try:
                # Create a simple synthetic flow
                src_ip = f"192.168.1.{random.randint(2,250)}"
                dst_ip = f"10.0.0.{random.randint(2,250)}"
                src_port = random.randint(1025, 65535)
                dst_port = random.choice([80, 443, 22, 53, 3389, 8080, 23])
                protocol = random.choice(['TCP', 'UDP'])

                flow = Flow(src_ip, dst_ip, src_port, dst_port, protocol)

                # Populate with a few packets
                now = time.time()
                pkt_count = random.randint(1, 10)
                for i in range(pkt_count):
                    size = random.randint(40, 1500)
                    direction = random.choice(['forward', 'backward'])
                    ts = now + i * 0.01
                    flow.add_packet(size, direction, ts, flags=None)

                # Mark as expired by putting it into the expired_flows queue
                self.expired_flows.put(flow)

                # Sleep a bit before generating next flow
                time.sleep(random.uniform(0.5, 2.0))
            except Exception as e:
                logger.error(f"Error in mock loop: {e}")
                time.sleep(1)

