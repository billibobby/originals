"""
Node model for The Originals.
Handles multi-computer network management and server deployment.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, Index
from sqlalchemy.orm import validates
import json
import re

# Import db from main app (will be initialized properly)
db = SQLAlchemy()


class Node(db.Model):
    """Node model for managing multiple computers in the network."""
    
    __tablename__ = 'nodes'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    hostname = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)  # Supports IPv6
    port = db.Column(db.Integer, default=3000, nullable=False)
    
    # SSH connection details
    ssh_port = db.Column(db.Integer, default=22)
    ssh_username = db.Column(db.String(100))
    ssh_key_path = db.Column(db.String(500))  # Path to SSH private key
    
    # Node status and metadata
    status = db.Column(db.Enum('online', 'offline', 'connecting', 'error', name='node_status'), 
                      default='offline', nullable=False)
    
    # Capabilities and specifications (stored as JSON)
    capabilities = db.Column(db.Text)  # JSON: cpu_cores, ram_gb, disk_gb, os, etc.
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_seen = db.Column(db.DateTime)
    last_heartbeat = db.Column(db.DateTime)
    
    # Node role and configuration
    is_master = db.Column(db.Boolean, default=False, nullable=False)
    is_enabled = db.Column(db.Boolean, default=True, nullable=False)
    max_servers = db.Column(db.Integer, default=5)  # Maximum servers this node can run
    
    # Performance and monitoring
    current_load = db.Column(db.Float, default=0.0)  # Current CPU load percentage
    memory_usage = db.Column(db.Float, default=0.0)  # Current memory usage percentage
    disk_usage = db.Column(db.Float, default=0.0)    # Current disk usage percentage
    
    # Configuration and settings (stored as JSON)
    config = db.Column(db.Text)  # JSON: specific node configuration
    
    # Relationships
    servers = db.relationship('ServerInstance', backref='node', lazy='dynamic')
    
    # Database constraints
    __table_args__ = (
        CheckConstraint('port > 0 AND port <= 65535', name='valid_port_range'),
        CheckConstraint('ssh_port > 0 AND ssh_port <= 65535', name='valid_ssh_port_range'),
        CheckConstraint('max_servers >= 0', name='max_servers_positive'),
        CheckConstraint('current_load >= 0.0 AND current_load <= 100.0', name='valid_load_range'),
        CheckConstraint('memory_usage >= 0.0 AND memory_usage <= 100.0', name='valid_memory_range'),
        CheckConstraint('disk_usage >= 0.0 AND disk_usage <= 100.0', name='valid_disk_range'),
        CheckConstraint('length(name) >= 3', name='name_min_length'),
        Index('idx_node_status_enabled', 'status', 'is_enabled'),
        Index('idx_node_ip_port', 'ip_address', 'port'),
        Index('idx_node_last_seen', 'last_seen'),
    )
    
    def __repr__(self):
        """String representation of node."""
        return f'<Node {self.name} ({self.ip_address}:{self.port})>'
    
    @validates('name')
    def validate_name(self, key, name):
        """Validate node name."""
        if not name or len(name.strip()) < 3:
            raise ValueError('Node name must be at least 3 characters')
        
        if len(name) > 100:
            raise ValueError('Node name must be no more than 100 characters')
        
        # Allow alphanumeric, spaces, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9_\-\s]+$', name):
            raise ValueError('Node name contains invalid characters')
        
        return name.strip()
    
    @validates('ip_address')
    def validate_ip_address(self, key, ip_address):
        """Validate IP address format."""
        import ipaddress as ip_module
        
        try:
            ip_module.ip_address(ip_address)
            return ip_address
        except ValueError:
            raise ValueError('Invalid IP address format')
    
    @validates('port', 'ssh_port')
    def validate_port(self, key, port):
        """Validate port numbers."""
        if not isinstance(port, int) or port < 1 or port > 65535:
            raise ValueError(f'{key} must be between 1 and 65535')
        return port
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get node capabilities as dictionary.
        
        Returns:
            Dictionary of node capabilities
        """
        if not self.capabilities:
            return {}
        
        try:
            return json.loads(self.capabilities)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_capabilities(self, capabilities: Optional[Dict[str, Any]]) -> None:
        """
        Set node capabilities from dictionary.
        
        Args:
            capabilities: Dictionary of capabilities
        """
        if capabilities is not None:
            self.capabilities = json.dumps(capabilities)
        else:
            self.capabilities = None
    
    def update_capabilities(self, **kwargs) -> None:
        """
        Update specific capability values.
        
        Args:
            **kwargs: Capability key-value pairs to update
        """
        caps = self.get_capabilities()
        caps.update(kwargs)
        self.set_capabilities(caps)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get node configuration as dictionary.
        
        Returns:
            Dictionary of node configuration
        """
        if not self.config:
            return {}
        
        try:
            return json.loads(self.config)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_config(self, config: Dict[str, Any]) -> None:
        """
        Set node configuration from dictionary.
        
        Args:
            config: Dictionary of configuration
        """
        self.config = json.dumps(config)
    
    def update_config(self, **kwargs) -> None:
        """
        Update specific configuration values.
        
        Args:
            **kwargs: Configuration key-value pairs to update
        """
        cfg = self.get_config()
        cfg.update(kwargs)
        self.set_config(cfg)
    
    def update_status(self, status: str, heartbeat: bool = True) -> None:
        """
        Update node status and timestamps.
        
        Args:
            status: New status value
            heartbeat: Whether to update last_heartbeat timestamp
        """
        valid_statuses = ['online', 'offline', 'connecting', 'error']
        if status not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        
        self.status = status
        self.updated_at = datetime.utcnow()
        
        if status == 'online':
            self.last_seen = datetime.utcnow()
        
        if heartbeat:
            self.last_heartbeat = datetime.utcnow()
    
    def update_performance_metrics(self, cpu_load: Optional[float] = None, 
                                 memory_usage: Optional[float] = None, 
                                 disk_usage: Optional[float] = None) -> None:
        """
        Update performance metrics for the node.
        
        Args:
            cpu_load: CPU load percentage (0-100)
            memory_usage: Memory usage percentage (0-100)
            disk_usage: Disk usage percentage (0-100)
        """
        if cpu_load is not None:
            if 0 <= cpu_load <= 100:
                self.current_load = cpu_load
        
        if memory_usage is not None:
            if 0 <= memory_usage <= 100:
                self.memory_usage = memory_usage
        
        if disk_usage is not None:
            if 0 <= disk_usage <= 100:
                self.disk_usage = disk_usage
        
        self.updated_at = datetime.utcnow()
    
    def is_available_for_deployment(self) -> bool:
        """
        Check if node is available for new server deployment.
        
        Returns:
            True if available, False otherwise
        """
        if not self.is_enabled or self.status != 'online':
            return False
        
        # Check server capacity
        current_servers = self.servers.filter_by(status='running').count()
        if current_servers >= self.max_servers:
            return False
        
        # Check resource usage
        if self.current_load > 80 or self.memory_usage > 85:
            return False
        
        return True
    
    def get_resource_usage(self) -> Dict[str, float]:
        """
        Get current resource usage summary.
        
        Returns:
            Dictionary with resource usage percentages
        """
        return {
            'cpu': self.current_load,
            'memory': self.memory_usage,
            'disk': self.disk_usage,
            'servers': (self.servers.count() / self.max_servers * 100) if self.max_servers > 0 else 0
        }
    
    def can_connect_via_ssh(self) -> bool:
        """
        Check if node has SSH connection configured.
        
        Returns:
            True if SSH is configured, False otherwise
        """
        return bool(self.ssh_username and (self.ssh_key_path or True))  # Password auth also possible
    
    def get_connection_string(self) -> str:
        """
        Get connection string for this node.
        
        Returns:
            Connection string in format: protocol://host:port
        """
        return f"http://{self.ip_address}:{self.port}"
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convert node to dictionary representation.
        
        Args:
            include_sensitive: Whether to include sensitive information
            
        Returns:
            Dictionary representation of node
        """
        data = {
            'id': self.id,
            'name': self.name,
            'hostname': self.hostname,
            'ip_address': self.ip_address,
            'port': self.port,
            'status': self.status,
            'is_master': self.is_master,
            'is_enabled': self.is_enabled,
            'max_servers': self.max_servers,
            'capabilities': self.get_capabilities(),
            'resource_usage': self.get_resource_usage(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'is_available': self.is_available_for_deployment(),
            'connection_string': self.get_connection_string(),
            'server_count': self.servers.count()
        }
        
        if include_sensitive:
            data.update({
                'ssh_port': self.ssh_port,
                'ssh_username': self.ssh_username,
                'ssh_key_path': self.ssh_key_path,
                'config': self.get_config()
            })
        
        return data
    
    @staticmethod
    def get_master_node() -> Optional['Node']:
        """
        Get the master node.
        
        Returns:
            Master node if exists, None otherwise
        """
        return Node.query.filter_by(is_master=True, is_enabled=True).first()
    
    @staticmethod
    def get_available_nodes() -> List['Node']:
        """
        Get all nodes available for deployment.
        
        Returns:
            List of available nodes
        """
        return [node for node in Node.query.filter_by(
            status='online', is_enabled=True
        ).all() if node.is_available_for_deployment()]
    
    @staticmethod
    def get_nodes_by_status(status: str) -> List['Node']:
        """
        Get nodes by status.
        
        Args:
            status: Node status to filter by
            
        Returns:
            List of nodes with specified status
        """
        return Node.query.filter_by(status=status).all()
    
    @staticmethod
    def create_master_node(name: str, ip_address: str, port: int = 3000, 
                          capabilities: Optional[Dict[str, Any]] = None) -> 'Node':
        """
        Create or update the master node.
        
        Args:
            name: Node name
            ip_address: IP address
            port: Port number
            capabilities: Node capabilities
            
        Returns:
            Created or updated master node
        """
        # Check if master node already exists
        existing_master = Node.get_master_node()
        if existing_master:
            existing_master.name = name
            existing_master.ip_address = ip_address
            existing_master.port = port
            existing_master.status = 'online'
            existing_master.last_seen = datetime.utcnow()
            if capabilities:
                existing_master.set_capabilities(capabilities)
            return existing_master
        
        # Create new master node
        master = Node(
            name=name,
            hostname=name.split()[0] if ' ' in name else name,  # Extract hostname from name
            ip_address=ip_address,
            port=port,
            is_master=True,
            status='online',
            last_seen=datetime.utcnow()
        )
        
        if capabilities:
            master.set_capabilities(capabilities)
        
        db.session.add(master)
        db.session.commit()
        
        return master 