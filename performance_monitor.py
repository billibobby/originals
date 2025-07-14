#!/usr/bin/env python3
"""
Performance Monitoring System for The Originals
Tracks system metrics, server performance, and user activity
"""

import os
import json
import time
import psutil
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from collections import deque
import logging
from threading import Lock
import sqlite3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    network_sent_mb: float
    network_recv_mb: float
    processes: int
    uptime_seconds: int

@dataclass
class ServerMetrics:
    """Minecraft server performance metrics"""
    timestamp: str
    status: str
    tps: float
    players_online: int
    memory_used_mb: float
    memory_allocated_mb: float
    world_size_mb: float
    entities_count: int
    chunks_loaded: int
    plugin_count: int

@dataclass
class UserActivity:
    """User activity tracking"""
    timestamp: str
    user_id: int
    username: str
    action: str
    details: str
    ip_address: str
    user_agent: str

@dataclass
class PerformanceAlert:
    """Performance alert data"""
    timestamp: str
    alert_type: str
    severity: str  # low, medium, high, critical
    message: str
    metric_name: str
    metric_value: float
    threshold: float
    acknowledged: bool = False

class PerformanceMonitor:
    """Comprehensive performance monitoring system"""
    
    def __init__(self, db_path: str = "performance_metrics.db"):
        self.db_path = db_path
        self.is_running = False
        self.monitor_thread = None
        self.metrics_lock = Lock()
        
        # In-memory storage for recent metrics
        self.recent_system_metrics = deque(maxlen=720)  # 12 hours of 1-minute data
        self.recent_server_metrics = deque(maxlen=720)
        self.recent_user_activity = deque(maxlen=1000)
        self.active_alerts = []
        
        # Performance thresholds
        self.thresholds = {
            'cpu_percent': {'high': 80, 'critical': 95},
            'memory_percent': {'high': 85, 'critical': 95},
            'disk_percent': {'high': 85, 'critical': 95},
            'server_tps': {'low': 15, 'critical': 10},
            'response_time': {'high': 5000, 'critical': 10000}  # milliseconds
        }
        
        # Initialize database
        self._init_database()
        
        # Network stats baseline
        self.network_stats = psutil.net_io_counters()
        self.last_network_time = time.time()
    
    def _init_database(self):
        """Initialize SQLite database for metrics storage"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # System metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        cpu_percent REAL,
                        memory_percent REAL,
                        memory_used_mb REAL,
                        memory_total_mb REAL,
                        disk_percent REAL,
                        disk_used_gb REAL,
                        disk_total_gb REAL,
                        network_sent_mb REAL,
                        network_recv_mb REAL,
                        processes INTEGER,
                        uptime_seconds INTEGER
                    )
                ''')
                
                # Server metrics table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS server_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        status TEXT,
                        tps REAL,
                        players_online INTEGER,
                        memory_used_mb REAL,
                        memory_allocated_mb REAL,
                        world_size_mb REAL,
                        entities_count INTEGER,
                        chunks_loaded INTEGER,
                        plugin_count INTEGER
                    )
                ''')
                
                # User activity table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS user_activity (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        user_id INTEGER,
                        username TEXT,
                        action TEXT,
                        details TEXT,
                        ip_address TEXT,
                        user_agent TEXT
                    )
                ''')
                
                # Performance alerts table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS performance_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        alert_type TEXT,
                        severity TEXT,
                        message TEXT,
                        metric_name TEXT,
                        metric_value REAL,
                        threshold REAL,
                        acknowledged BOOLEAN DEFAULT FALSE
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_timestamp ON system_metrics(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_server_timestamp ON server_metrics(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_timestamp ON user_activity(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON performance_alerts(timestamp)')
                
                conn.commit()
                logger.info("Performance monitoring database initialized")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    def start_monitoring(self):
        """Start performance monitoring"""
        if self.is_running:
            logger.warning("Performance monitoring already running")
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        if not self.is_running:
            return
        
        self.is_running = False
        
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        
        logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                if system_metrics:
                    with self.metrics_lock:
                        self.recent_system_metrics.append(system_metrics)
                    self._store_system_metrics(system_metrics)
                    self._check_system_alerts(system_metrics)
                
                # Collect server metrics
                server_metrics = self._collect_server_metrics()
                if server_metrics:
                    with self.metrics_lock:
                        self.recent_server_metrics.append(server_metrics)
                    self._store_server_metrics(server_metrics)
                    self._check_server_alerts(server_metrics)
                
                # Sleep for 1 minute
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                time.sleep(60)
    
    def _collect_system_metrics(self) -> Optional[SystemMetrics]:
        """Collect system performance metrics"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_used_mb = (memory.total - memory.available) / (1024 * 1024)
            memory_total_mb = memory.total / (1024 * 1024)
            
            # Disk usage
            disk_usage = psutil.disk_usage('/')
            disk_used_gb = disk_usage.used / (1024 * 1024 * 1024)
            disk_total_gb = disk_usage.total / (1024 * 1024 * 1024)
            disk_percent = (disk_usage.used / disk_usage.total) * 100
            
            # Network usage
            current_net = psutil.net_io_counters()
            current_time = time.time()
            time_diff = current_time - self.last_network_time
            
            if time_diff > 0:
                network_sent_mb = (current_net.bytes_sent - self.network_stats.bytes_sent) / (1024 * 1024)
                network_recv_mb = (current_net.bytes_recv - self.network_stats.bytes_recv) / (1024 * 1024)
            else:
                network_sent_mb = 0
                network_recv_mb = 0
            
            self.network_stats = current_net
            self.last_network_time = current_time
            
            # Process count
            processes = len(psutil.pids())
            
            # System uptime
            uptime_seconds = int(time.time() - psutil.boot_time())
            
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory_used_mb,
                memory_total_mb=memory_total_mb,
                disk_percent=disk_percent,
                disk_used_gb=disk_used_gb,
                disk_total_gb=disk_total_gb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb,
                processes=processes,
                uptime_seconds=uptime_seconds
            )
            
        except Exception as e:
            logger.error(f"System metrics collection failed: {e}")
            return None
    
    def _collect_server_metrics(self) -> Optional[ServerMetrics]:
        """Collect Minecraft server performance metrics"""
        try:
            # This would integrate with your server manager
            # For now, we'll use placeholder data
            
            # Check if server process is running
            server_running = self._is_server_running()
            
            if not server_running:
                return ServerMetrics(
                    timestamp=datetime.now().isoformat(),
                    status="stopped",
                    tps=0,
                    players_online=0,
                    memory_used_mb=0,
                    memory_allocated_mb=0,
                    world_size_mb=0,
                    entities_count=0,
                    chunks_loaded=0,
                    plugin_count=0
                )
            
            # Get server process metrics
            server_process = self._get_server_process()
            if server_process:
                memory_info = server_process.memory_info()
                memory_used_mb = memory_info.rss / (1024 * 1024)
            else:
                memory_used_mb = 0
            
            # Get world size
            world_size_mb = self._get_world_size()
            
            return ServerMetrics(
                timestamp=datetime.now().isoformat(),
                status="running",
                tps=20.0,  # Would be parsed from server logs
                players_online=0,  # Would be parsed from server logs
                memory_used_mb=memory_used_mb,
                memory_allocated_mb=1024,  # Would be configured
                world_size_mb=world_size_mb,
                entities_count=0,  # Would be parsed from server logs
                chunks_loaded=0,  # Would be parsed from server logs
                plugin_count=0  # Would be scanned from plugins directory
            )
            
        except Exception as e:
            logger.error(f"Server metrics collection failed: {e}")
            return None
    
    def _is_server_running(self) -> bool:
        """Check if Minecraft server is running"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if 'fabric-server-launch' in cmdline or 'minecraft_server' in cmdline:
                        return True
            return False
        except Exception:
            return False
    
    def _get_server_process(self) -> Optional[psutil.Process]:
        """Get the Minecraft server process"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['cmdline']:
                    cmdline = ' '.join(proc.info['cmdline'])
                    if 'fabric-server-launch' in cmdline or 'minecraft_server' in cmdline:
                        return proc
            return None
        except Exception:
            return None
    
    def _get_world_size(self) -> float:
        """Get world directory size in MB"""
        try:
            world_dir = Path("minecraft_server/world")
            if world_dir.exists():
                total_size = sum(f.stat().st_size for f in world_dir.rglob('*') if f.is_file())
                return total_size / (1024 * 1024)
            return 0
        except Exception:
            return 0
    
    def _store_system_metrics(self, metrics: SystemMetrics):
        """Store system metrics in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO system_metrics (
                        timestamp, cpu_percent, memory_percent, memory_used_mb, memory_total_mb,
                        disk_percent, disk_used_gb, disk_total_gb, network_sent_mb, network_recv_mb,
                        processes, uptime_seconds
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metrics.timestamp, metrics.cpu_percent, metrics.memory_percent,
                    metrics.memory_used_mb, metrics.memory_total_mb, metrics.disk_percent,
                    metrics.disk_used_gb, metrics.disk_total_gb, metrics.network_sent_mb,
                    metrics.network_recv_mb, metrics.processes, metrics.uptime_seconds
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store system metrics: {e}")
    
    def _store_server_metrics(self, metrics: ServerMetrics):
        """Store server metrics in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO server_metrics (
                        timestamp, status, tps, players_online, memory_used_mb, memory_allocated_mb,
                        world_size_mb, entities_count, chunks_loaded, plugin_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metrics.timestamp, metrics.status, metrics.tps, metrics.players_online,
                    metrics.memory_used_mb, metrics.memory_allocated_mb, metrics.world_size_mb,
                    metrics.entities_count, metrics.chunks_loaded, metrics.plugin_count
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store server metrics: {e}")
    
    def _check_system_alerts(self, metrics: SystemMetrics):
        """Check for system performance alerts"""
        alerts = []
        
        # CPU usage alerts
        if metrics.cpu_percent >= self.thresholds['cpu_percent']['critical']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                alert_type="system",
                severity="critical",
                message=f"Critical CPU usage: {metrics.cpu_percent:.1f}%",
                metric_name="cpu_percent",
                metric_value=metrics.cpu_percent,
                threshold=self.thresholds['cpu_percent']['critical']
            ))
        elif metrics.cpu_percent >= self.thresholds['cpu_percent']['high']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                alert_type="system",
                severity="high",
                message=f"High CPU usage: {metrics.cpu_percent:.1f}%",
                metric_name="cpu_percent",
                metric_value=metrics.cpu_percent,
                threshold=self.thresholds['cpu_percent']['high']
            ))
        
        # Memory usage alerts
        if metrics.memory_percent >= self.thresholds['memory_percent']['critical']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                alert_type="system",
                severity="critical",
                message=f"Critical memory usage: {metrics.memory_percent:.1f}%",
                metric_name="memory_percent",
                metric_value=metrics.memory_percent,
                threshold=self.thresholds['memory_percent']['critical']
            ))
        elif metrics.memory_percent >= self.thresholds['memory_percent']['high']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                alert_type="system",
                severity="high",
                message=f"High memory usage: {metrics.memory_percent:.1f}%",
                metric_name="memory_percent",
                metric_value=metrics.memory_percent,
                threshold=self.thresholds['memory_percent']['high']
            ))
        
        # Disk usage alerts
        if metrics.disk_percent >= self.thresholds['disk_percent']['critical']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                alert_type="system",
                severity="critical",
                message=f"Critical disk usage: {metrics.disk_percent:.1f}%",
                metric_name="disk_percent",
                metric_value=metrics.disk_percent,
                threshold=self.thresholds['disk_percent']['critical']
            ))
        elif metrics.disk_percent >= self.thresholds['disk_percent']['high']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                alert_type="system",
                severity="high",
                message=f"High disk usage: {metrics.disk_percent:.1f}%",
                metric_name="disk_percent",
                metric_value=metrics.disk_percent,
                threshold=self.thresholds['disk_percent']['high']
            ))
        
        # Store alerts
        for alert in alerts:
            self._store_alert(alert)
            with self.metrics_lock:
                self.active_alerts.append(alert)
    
    def _check_server_alerts(self, metrics: ServerMetrics):
        """Check for server performance alerts"""
        if metrics.status != "running":
            return
        
        alerts = []
        
        # TPS alerts
        if metrics.tps <= self.thresholds['server_tps']['critical']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                alert_type="server",
                severity="critical",
                message=f"Critical server TPS: {metrics.tps:.1f}",
                metric_name="server_tps",
                metric_value=metrics.tps,
                threshold=self.thresholds['server_tps']['critical']
            ))
        elif metrics.tps <= self.thresholds['server_tps']['low']:
            alerts.append(PerformanceAlert(
                timestamp=metrics.timestamp,
                alert_type="server",
                severity="high",
                message=f"Low server TPS: {metrics.tps:.1f}",
                metric_name="server_tps",
                metric_value=metrics.tps,
                threshold=self.thresholds['server_tps']['low']
            ))
        
        # Store alerts
        for alert in alerts:
            self._store_alert(alert)
            with self.metrics_lock:
                self.active_alerts.append(alert)
    
    def _store_alert(self, alert: PerformanceAlert):
        """Store performance alert in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO performance_alerts (
                        timestamp, alert_type, severity, message, metric_name, metric_value, threshold
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert.timestamp, alert.alert_type, alert.severity, alert.message,
                    alert.metric_name, alert.metric_value, alert.threshold
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to store alert: {e}")
    
    def track_user_activity(self, user_id: int, username: str, action: str, 
                           details: str = "", ip_address: str = "", user_agent: str = ""):
        """Track user activity"""
        try:
            activity = UserActivity(
                timestamp=datetime.now().isoformat(),
                user_id=user_id,
                username=username,
                action=action,
                details=details,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            with self.metrics_lock:
                self.recent_user_activity.append(activity)
            
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO user_activity (
                        timestamp, user_id, username, action, details, ip_address, user_agent
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    activity.timestamp, activity.user_id, activity.username, activity.action,
                    activity.details, activity.ip_address, activity.user_agent
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to track user activity: {e}")
    
    def get_recent_metrics(self, hours: int = 1) -> Dict[str, Any]:
        """Get recent performance metrics"""
        try:
            with self.metrics_lock:
                # Calculate how many records to include (1 per minute)
                records_to_include = min(hours * 60, len(self.recent_system_metrics))
                
                system_metrics = list(self.recent_system_metrics)[-records_to_include:]
                server_metrics = list(self.recent_server_metrics)[-records_to_include:]
                user_activity = list(self.recent_user_activity)[-100:]  # Last 100 activities
                
                return {
                    'system_metrics': [asdict(m) for m in system_metrics],
                    'server_metrics': [asdict(m) for m in server_metrics],
                    'user_activity': [asdict(a) for a in user_activity],
                    'active_alerts': [asdict(a) for a in self.active_alerts[-50:]],  # Last 50 alerts
                    'summary': self._get_metrics_summary()
                }
                
        except Exception as e:
            logger.error(f"Failed to get recent metrics: {e}")
            return {}
    
    def _get_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of current metrics"""
        try:
            with self.metrics_lock:
                if not self.recent_system_metrics:
                    return {}
                
                latest_system = self.recent_system_metrics[-1]
                latest_server = self.recent_server_metrics[-1] if self.recent_server_metrics else None
                
                return {
                    'current_cpu': latest_system.cpu_percent,
                    'current_memory': latest_system.memory_percent,
                    'current_disk': latest_system.disk_percent,
                    'server_status': latest_server.status if latest_server else "unknown",
                    'server_tps': latest_server.tps if latest_server else 0,
                    'players_online': latest_server.players_online if latest_server else 0,
                    'active_alerts_count': len(self.active_alerts),
                    'uptime_hours': latest_system.uptime_seconds / 3600,
                    'monitoring_status': 'running' if self.is_running else 'stopped'
                }
                
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {}
    
    def get_historical_metrics(self, hours: int = 24) -> Dict[str, Any]:
        """Get historical metrics from database"""
        try:
            start_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get system metrics
                cursor.execute('''
                    SELECT * FROM system_metrics 
                    WHERE timestamp >= ? 
                    ORDER BY timestamp DESC
                ''', (start_time,))
                system_metrics = cursor.fetchall()
                
                # Get server metrics
                cursor.execute('''
                    SELECT * FROM server_metrics 
                    WHERE timestamp >= ? 
                    ORDER BY timestamp DESC
                ''', (start_time,))
                server_metrics = cursor.fetchall()
                
                # Get user activity
                cursor.execute('''
                    SELECT * FROM user_activity 
                    WHERE timestamp >= ? 
                    ORDER BY timestamp DESC
                    LIMIT 1000
                ''', (start_time,))
                user_activity = cursor.fetchall()
                
                # Get alerts
                cursor.execute('''
                    SELECT * FROM performance_alerts 
                    WHERE timestamp >= ? 
                    ORDER BY timestamp DESC
                ''', (start_time,))
                alerts = cursor.fetchall()
                
                return {
                    'system_metrics': system_metrics,
                    'server_metrics': server_metrics,
                    'user_activity': user_activity,
                    'alerts': alerts,
                    'period_hours': hours
                }
                
        except Exception as e:
            logger.error(f"Failed to get historical metrics: {e}")
            return {}
    
    def acknowledge_alert(self, alert_id: int):
        """Acknowledge a performance alert"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE performance_alerts 
                    SET acknowledged = TRUE 
                    WHERE id = ?
                ''', (alert_id,))
                conn.commit()
                
            # Remove from active alerts
            with self.metrics_lock:
                self.active_alerts = [a for a in self.active_alerts if a.timestamp != alert_id]
                
        except Exception as e:
            logger.error(f"Failed to acknowledge alert: {e}")
    
    def cleanup_old_data(self, days: int = 30):
        """Clean up old performance data"""
        try:
            cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clean up old metrics
                cursor.execute('DELETE FROM system_metrics WHERE timestamp < ?', (cutoff_time,))
                cursor.execute('DELETE FROM server_metrics WHERE timestamp < ?', (cutoff_time,))
                cursor.execute('DELETE FROM user_activity WHERE timestamp < ?', (cutoff_time,))
                cursor.execute('DELETE FROM performance_alerts WHERE timestamp < ?', (cutoff_time,))
                
                conn.commit()
                
                # Vacuum database to reclaim space
                cursor.execute('VACUUM')
                
            logger.info(f"Cleaned up performance data older than {days} days")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")

# Global performance monitor instance
performance_monitor = None

def get_performance_monitor() -> PerformanceMonitor:
    """Get or create performance monitor instance"""
    global performance_monitor
    if performance_monitor is None:
        performance_monitor = PerformanceMonitor()
    return performance_monitor

def initialize_performance_monitoring():
    """Initialize and start performance monitoring"""
    monitor = get_performance_monitor()
    monitor.start_monitoring()
    logger.info("Performance monitoring initialized")
    return monitor

if __name__ == "__main__":
    # Test the performance monitoring system
    monitor = PerformanceMonitor()
    monitor.start_monitoring()
    
    # Let it run for a bit
    time.sleep(10)
    
    # Get recent metrics
    metrics = monitor.get_recent_metrics(hours=1)
    print(f"Recent metrics: {metrics}")
    
    # Stop monitoring
    monitor.stop_monitoring() 