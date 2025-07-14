"""
ServerInstance model for The Originals.
Handles Minecraft server instance management and configuration.
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


class ServerInstance(db.Model):
    """ServerInstance model for managing individual Minecraft servers."""
    
    __tablename__ = 'server_instances'
    
    # Primary fields
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Server configuration
    minecraft_version = db.Column(db.String(20), default='1.20.1', nullable=False)
    server_type = db.Column(db.Enum('fabric', 'forge', 'vanilla', 'paper', 'spigot', name='server_types'), 
                           default='fabric', nullable=False)
    
    # Network configuration
    port = db.Column(db.Integer, default=25565, nullable=False)
    rcon_port = db.Column(db.Integer, default=25575)
    query_port = db.Column(db.Integer, default=25565)
    
    # Server settings
    max_players = db.Column(db.Integer, default=20, nullable=False)
    difficulty = db.Column(db.Enum('peaceful', 'easy', 'normal', 'hard', name='difficulty_levels'), 
                          default='normal', nullable=False)
    gamemode = db.Column(db.Enum('survival', 'creative', 'adventure', 'spectator', name='game_modes'), 
                        default='survival', nullable=False)
    
    # World settings
    world_name = db.Column(db.String(100), default='world', nullable=False)
    seed = db.Column(db.String(50))  # Minecraft world seed
    generate_structures = db.Column(db.Boolean, default=True, nullable=False)
    
    # Server status and metadata
    status = db.Column(db.Enum('stopped', 'starting', 'running', 'stopping', 'crashed', name='server_status'), 
                      default='stopped', nullable=False)
    
    # Configuration (stored as JSON)
    config = db.Column(db.Text)  # JSON: server.properties and other configs
    mod_list = db.Column(db.Text)  # JSON: list of installed mods
    
    # Performance and monitoring
    cpu_usage = db.Column(db.Float, default=0.0)
    memory_usage = db.Column(db.Integer, default=0)  # MB
    memory_limit = db.Column(db.Integer, default=2048)  # MB
    player_count = db.Column(db.Integer, default=0)
    tps = db.Column(db.Float, default=20.0)  # Ticks per second
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_started = db.Column(db.DateTime)
    last_stopped = db.Column(db.DateTime)
    last_activity = db.Column(db.DateTime)
    
    # Relationships
    node_id = db.Column(db.Integer, db.ForeignKey('nodes.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Auto-management settings
    auto_start = db.Column(db.Boolean, default=False, nullable=False)
    auto_restart = db.Column(db.Boolean, default=True, nullable=False)
    restart_schedule = db.Column(db.String(100))  # Cron-like schedule string
    
    # Backup settings
    auto_backup = db.Column(db.Boolean, default=True, nullable=False)
    backup_interval = db.Column(db.Integer, default=24)  # Hours
    last_backup = db.Column(db.DateTime)
    
    # Database constraints
    __table_args__ = (
        CheckConstraint('port > 0 AND port <= 65535', name='valid_port_range'),
        CheckConstraint('rcon_port > 0 AND rcon_port <= 65535', name='valid_rcon_port_range'),
        CheckConstraint('query_port > 0 AND query_port <= 65535', name='valid_query_port_range'),
        CheckConstraint('max_players > 0 AND max_players <= 999', name='valid_max_players'),
        CheckConstraint('memory_usage >= 0', name='memory_usage_positive'),
        CheckConstraint('memory_limit > 0', name='memory_limit_positive'),
        CheckConstraint('player_count >= 0', name='player_count_positive'),
        CheckConstraint('tps >= 0.0 AND tps <= 20.0', name='valid_tps_range'),
        CheckConstraint('cpu_usage >= 0.0 AND cpu_usage <= 100.0', name='valid_cpu_range'),
        CheckConstraint('backup_interval > 0', name='backup_interval_positive'),
        CheckConstraint('length(name) >= 3', name='name_min_length'),
        Index('idx_server_status_node', 'status', 'node_id'),
        Index('idx_server_created_by', 'created_by'),
        Index('idx_server_last_started', 'last_started'),
    )
    
    def __repr__(self):
        """String representation of server instance."""
        return f'<ServerInstance {self.name} ({self.status})>'
    
    @validates('name')
    def validate_name(self, key, name):
        """Validate server name."""
        if not name or len(name.strip()) < 3:
            raise ValueError('Server name must be at least 3 characters')
        
        if len(name) > 100:
            raise ValueError('Server name must be no more than 100 characters')
        
        # Allow alphanumeric, spaces, hyphens, underscores
        if not re.match(r'^[a-zA-Z0-9_\-\s]+$', name):
            raise ValueError('Server name contains invalid characters')
        
        return name.strip()
    
    @validates('minecraft_version')
    def validate_minecraft_version(self, key, version):
        """Validate Minecraft version format."""
        if not version:
            raise ValueError('Minecraft version is required')
        
        # Basic version format validation (e.g., 1.20.1, 1.19, etc.)
        if not re.match(r'^\d+\.\d+(?:\.\d+)?$', version):
            raise ValueError('Invalid Minecraft version format')
        
        return version
    
    @validates('port', 'rcon_port', 'query_port')
    def validate_port(self, key, port):
        """Validate port numbers."""
        if port is not None and (not isinstance(port, int) or port < 1 or port > 65535):
            raise ValueError(f'{key} must be between 1 and 65535')
        return port
    
    @validates('max_players')
    def validate_max_players(self, key, max_players):
        """Validate max players setting."""
        if not isinstance(max_players, int) or max_players < 1 or max_players > 999:
            raise ValueError('Max players must be between 1 and 999')
        return max_players
    
    @validates('world_name')
    def validate_world_name(self, key, world_name):
        """Validate world name."""
        if not world_name:
            raise ValueError('World name is required')
        
        # World names should be filesystem-safe
        if not re.match(r'^[a-zA-Z0-9_\-]{1,50}$', world_name):
            raise ValueError('World name must be alphanumeric with underscores/hyphens only')
        
        return world_name
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get server configuration as dictionary.
        
        Returns:
            Dictionary of server configuration
        """
        if not self.config:
            return {}
        
        try:
            return json.loads(self.config)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_config(self, config: Optional[Dict[str, Any]]) -> None:
        """
        Set server configuration from dictionary.
        
        Args:
            config: Dictionary of configuration
        """
        if config is not None:
            self.config = json.dumps(config)
        else:
            self.config = None
    
    def update_config(self, **kwargs) -> None:
        """
        Update specific configuration values.
        
        Args:
            **kwargs: Configuration key-value pairs to update
        """
        cfg = self.get_config()
        cfg.update(kwargs)
        self.set_config(cfg)
    
    def get_mod_list(self) -> List[Dict[str, Any]]:
        """
        Get list of installed mods.
        
        Returns:
            List of mod information dictionaries
        """
        if not self.mod_list:
            return []
        
        try:
            return json.loads(self.mod_list)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_mod_list(self, mods: Optional[List[Dict[str, Any]]]) -> None:
        """
        Set list of installed mods.
        
        Args:
            mods: List of mod information dictionaries
        """
        if mods is not None:
            self.mod_list = json.dumps(mods)
        else:
            self.mod_list = None
    
    def add_mod(self, mod_info: Dict[str, Any]) -> None:
        """
        Add a mod to the server's mod list.
        
        Args:
            mod_info: Dictionary containing mod information
        """
        mods = self.get_mod_list()
        
        # Check if mod already exists (by filename or mod_id)
        mod_id = mod_info.get('mod_id')
        filename = mod_info.get('filename')
        
        for i, existing_mod in enumerate(mods):
            if (mod_id and existing_mod.get('mod_id') == mod_id) or \
               (filename and existing_mod.get('filename') == filename):
                mods[i] = mod_info  # Update existing mod
                self.set_mod_list(mods)
                return
        
        # Add new mod
        mods.append(mod_info)
        self.set_mod_list(mods)
    
    def remove_mod(self, mod_identifier: str) -> bool:
        """
        Remove a mod from the server's mod list.
        
        Args:
            mod_identifier: Mod ID or filename to remove
            
        Returns:
            True if mod was removed, False if not found
        """
        mods = self.get_mod_list()
        
        for i, mod in enumerate(mods):
            if mod.get('mod_id') == mod_identifier or mod.get('filename') == mod_identifier:
                mods.pop(i)
                self.set_mod_list(mods)
                return True
        
        return False
    
    def update_status(self, status: str, update_timestamps: bool = True) -> None:
        """
        Update server status with appropriate timestamp updates.
        
        Args:
            status: New status value
            update_timestamps: Whether to update relevant timestamps
        """
        valid_statuses = ['stopped', 'starting', 'running', 'stopping', 'crashed']
        if status not in valid_statuses:
            raise ValueError(f'Status must be one of: {", ".join(valid_statuses)}')
        
        old_status = self.status
        self.status = status
        self.updated_at = datetime.utcnow()
        
        if update_timestamps:
            if status == 'running' and old_status != 'running':
                self.last_started = datetime.utcnow()
            elif status == 'stopped' and old_status in ['running', 'stopping']:
                self.last_stopped = datetime.utcnow()
            
            if status in ['running', 'starting']:
                self.last_activity = datetime.utcnow()
    
    def update_performance_metrics(self, cpu_usage: Optional[float] = None, 
                                 memory_usage: Optional[int] = None,
                                 player_count: Optional[int] = None,
                                 tps: Optional[float] = None) -> None:
        """
        Update server performance metrics.
        
        Args:
            cpu_usage: CPU usage percentage (0-100)
            memory_usage: Memory usage in MB
            player_count: Current number of players
            tps: Current ticks per second
        """
        if cpu_usage is not None and 0 <= cpu_usage <= 100:
            self.cpu_usage = cpu_usage
        
        if memory_usage is not None and memory_usage >= 0:
            self.memory_usage = memory_usage
        
        if player_count is not None and player_count >= 0:
            self.player_count = player_count
        
        if tps is not None and 0 <= tps <= 20:
            self.tps = tps
        
        self.last_activity = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def is_running(self) -> bool:
        """Check if server is currently running."""
        return self.status == 'running'
    
    def can_start(self) -> bool:
        """Check if server can be started."""
        return self.status in ['stopped', 'crashed']
    
    def can_stop(self) -> bool:
        """Check if server can be stopped."""
        return self.status in ['running', 'starting']
    
    def needs_restart(self) -> bool:
        """Check if server needs to be restarted based on schedule."""
        if not self.restart_schedule or not self.last_started:
            return False
        
        # TODO: Implement cron-like schedule parsing
        # For now, just check if it's been running for more than 24 hours
        if self.status == 'running':
            hours_running = (datetime.utcnow() - self.last_started).total_seconds() / 3600
            return hours_running >= 24
        
        return False
    
    def needs_backup(self) -> bool:
        """Check if server needs a backup based on schedule."""
        if not self.auto_backup:
            return False
        
        if not self.last_backup:
            return True  # Never backed up
        
        hours_since_backup = (datetime.utcnow() - self.last_backup).total_seconds() / 3600
        return hours_since_backup >= self.backup_interval
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """
        Get current resource usage summary.
        
        Returns:
            Dictionary with resource usage information
        """
        memory_percent = (self.memory_usage / self.memory_limit * 100) if self.memory_limit > 0 else 0
        
        return {
            'cpu_percent': self.cpu_usage,
            'memory_mb': self.memory_usage,
            'memory_limit_mb': self.memory_limit,
            'memory_percent': memory_percent,
            'player_count': self.player_count,
            'max_players': self.max_players,
            'player_percent': (self.player_count / self.max_players * 100) if self.max_players > 0 else 0,
            'tps': self.tps,
            'tps_percent': (self.tps / 20.0 * 100) if self.tps > 0 else 0
        }
    
    def get_uptime(self) -> Optional[int]:
        """
        Get server uptime in seconds.
        
        Returns:
            Uptime in seconds if running, None otherwise
        """
        if self.status == 'running' and self.last_started:
            return int((datetime.utcnow() - self.last_started).total_seconds())
        return None
    
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convert server instance to dictionary representation.
        
        Args:
            include_sensitive: Whether to include sensitive information
            
        Returns:
            Dictionary representation of server instance
        """
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'minecraft_version': self.minecraft_version,
            'server_type': self.server_type,
            'port': self.port,
            'max_players': self.max_players,
            'difficulty': self.difficulty,
            'gamemode': self.gamemode,
            'world_name': self.world_name,
            'seed': self.seed,
            'status': self.status,
            'player_count': self.player_count,
            'tps': self.tps,
            'resource_usage': self.get_resource_usage(),
            'uptime': self.get_uptime(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_started': self.last_started.isoformat() if self.last_started else None,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'mod_count': len(self.get_mod_list()),
            'node_id': self.node_id,
            'created_by': self.created_by,
            'auto_start': self.auto_start,
            'auto_restart': self.auto_restart,
            'auto_backup': self.auto_backup,
            'needs_restart': self.needs_restart(),
            'needs_backup': self.needs_backup()
        }
        
        if include_sensitive:
            data.update({
                'rcon_port': self.rcon_port,
                'query_port': self.query_port,
                'config': self.get_config(),
                'mod_list': self.get_mod_list(),
                'restart_schedule': self.restart_schedule,
                'backup_interval': self.backup_interval,
                'last_backup': self.last_backup.isoformat() if self.last_backup else None
            })
        
        return data
    
    @staticmethod
    def get_running_servers() -> List['ServerInstance']:
        """Get all currently running servers."""
        return ServerInstance.query.filter_by(status='running').all()
    
    @staticmethod
    def get_servers_by_node(node_id: int) -> List['ServerInstance']:
        """
        Get all servers on a specific node.
        
        Args:
            node_id: Node ID to filter by
            
        Returns:
            List of servers on the specified node
        """
        return ServerInstance.query.filter_by(node_id=node_id).all()
    
    @staticmethod
    def get_servers_by_user(user_id: int) -> List['ServerInstance']:
        """
        Get all servers created by a specific user.
        
        Args:
            user_id: User ID to filter by
            
        Returns:
            List of servers created by the specified user
        """
        return ServerInstance.query.filter_by(created_by=user_id).all()
    
    @staticmethod
    def get_servers_needing_restart() -> List['ServerInstance']:
        """Get all servers that need to be restarted."""
        return [server for server in ServerInstance.get_running_servers() 
                if server.needs_restart()]
    
    @staticmethod
    def get_servers_needing_backup() -> List['ServerInstance']:
        """Get all servers that need to be backed up."""
        return [server for server in ServerInstance.query.all() 
                if server.needs_backup()] 