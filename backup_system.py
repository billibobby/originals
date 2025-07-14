#!/usr/bin/env python3
"""
Automated Backup System for The Originals
Handles database backups, configuration backups, and server world backups
"""

import os
import json
import shutil
import sqlite3
import tarfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import threading
import time
import logging
from dataclasses import dataclass
import schedule

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class BackupConfig:
    """Configuration for backup operations"""
    backup_dir: str = "backups"
    max_backups: int = 10
    backup_interval_hours: int = 24
    compress_backups: bool = True
    include_world_files: bool = True
    include_database: bool = True
    include_configs: bool = True
    include_logs: bool = False
    retention_days: int = 30

class BackupManager:
    """Comprehensive backup management system"""
    
    def __init__(self, config: BackupConfig = None):
        self.config = config or BackupConfig()
        self.backup_dir = Path(self.config.backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
        self.is_running = False
        self.scheduler_thread = None
        
        # Create subdirectories
        for subdir in ['database', 'configs', 'worlds', 'full']:
            (self.backup_dir / subdir).mkdir(exist_ok=True)
    
    def start_scheduler(self):
        """Start the automatic backup scheduler"""
        if self.is_running:
            logger.warning("Backup scheduler already running")
            return
        
        self.is_running = True
        
        # Schedule regular backups
        schedule.every(self.config.backup_interval_hours).hours.do(self.create_full_backup)
        
        # Schedule cleanup job
        schedule.every().day.at("02:00").do(self.cleanup_old_backups)
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info(f"Backup scheduler started (interval: {self.config.backup_interval_hours}h)")
    
    def stop_scheduler(self):
        """Stop the automatic backup scheduler"""
        if not self.is_running:
            return
        
        self.is_running = False
        schedule.clear()
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        logger.info("Backup scheduler stopped")
    
    def _run_scheduler(self):
        """Run the backup scheduler"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Backup scheduler error: {e}")
                time.sleep(300)  # Wait 5 minutes on error
    
    def create_full_backup(self) -> Tuple[bool, str]:
        """Create a complete backup of all components"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"full_backup_{timestamp}"
            backup_path = self.backup_dir / "full" / backup_name
            backup_path.mkdir(exist_ok=True)
            
            logger.info(f"Starting full backup: {backup_name}")
            
            # Create backup manifest
            manifest = {
                'backup_name': backup_name,
                'timestamp': timestamp,
                'created_at': datetime.now().isoformat(),
                'components': [],
                'status': 'in_progress'
            }
            
            # Backup database
            if self.config.include_database:
                success, message = self._backup_database(backup_path)
                manifest['components'].append({
                    'type': 'database',
                    'success': success,
                    'message': message
                })
            
            # Backup configurations
            if self.config.include_configs:
                success, message = self._backup_configs(backup_path)
                manifest['components'].append({
                    'type': 'configs',
                    'success': success,
                    'message': message
                })
            
            # Backup world files
            if self.config.include_world_files:
                success, message = self._backup_worlds(backup_path)
                manifest['components'].append({
                    'type': 'worlds',
                    'success': success,
                    'message': message
                })
            
            # Backup logs (if enabled)
            if self.config.include_logs:
                success, message = self._backup_logs(backup_path)
                manifest['components'].append({
                    'type': 'logs',
                    'success': success,
                    'message': message
                })
            
            # Finalize manifest
            manifest['status'] = 'completed'
            manifest['completed_at'] = datetime.now().isoformat()
            
            # Save manifest
            with open(backup_path / 'manifest.json', 'w') as f:
                json.dump(manifest, f, indent=2)
            
            # Compress if enabled
            if self.config.compress_backups:
                self._compress_backup(backup_path)
            
            logger.info(f"Full backup completed: {backup_name}")
            return True, f"Backup created successfully: {backup_name}"
            
        except Exception as e:
            logger.error(f"Full backup failed: {e}")
            return False, f"Backup failed: {str(e)}"
    
    def _backup_database(self, backup_path: Path) -> Tuple[bool, str]:
        """Backup the SQLite database"""
        try:
            db_path = Path("the_originals.db")
            if not db_path.exists():
                return False, "Database file not found"
            
            # Create database backup directory
            db_backup_dir = backup_path / "database"
            db_backup_dir.mkdir(exist_ok=True)
            
            # Copy database file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_db_path = db_backup_dir / f"database_{timestamp}.db"
            
            # Use SQLite backup API for consistent backup
            with sqlite3.connect(str(db_path)) as source:
                with sqlite3.connect(str(backup_db_path)) as backup:
                    source.backup(backup)
            
            # Create readable SQL dump
            sql_dump_path = db_backup_dir / f"database_{timestamp}.sql"
            with sqlite3.connect(str(db_path)) as conn:
                with open(sql_dump_path, 'w') as f:
                    for line in conn.iterdump():
                        f.write(f'{line}\n')
            
            logger.info(f"Database backup completed: {backup_db_path}")
            return True, f"Database backed up to {backup_db_path}"
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False, f"Database backup error: {str(e)}"
    
    def _backup_configs(self, backup_path: Path) -> Tuple[bool, str]:
        """Backup configuration files"""
        try:
            config_backup_dir = backup_path / "configs"
            config_backup_dir.mkdir(exist_ok=True)
            
            # Files to backup
            config_files = [
                'env_example.txt',
                'requirements.txt',
                'logging_config.py',
                'minecraft_server/server.properties',
                'minecraft_server/eula.txt',
                'minecraft_server/fabric-server-launcher.properties'
            ]
            
            backed_up = []
            for config_file in config_files:
                source_path = Path(config_file)
                if source_path.exists():
                    dest_path = config_backup_dir / source_path.name
                    shutil.copy2(source_path, dest_path)
                    backed_up.append(str(source_path))
            
            # Backup entire config directory if exists
            if Path('config').exists():
                shutil.copytree('config', config_backup_dir / 'config', dirs_exist_ok=True)
                backed_up.append('config/')
            
            logger.info(f"Config backup completed: {len(backed_up)} files")
            return True, f"Configs backed up: {', '.join(backed_up)}"
            
        except Exception as e:
            logger.error(f"Config backup failed: {e}")
            return False, f"Config backup error: {str(e)}"
    
    def _backup_worlds(self, backup_path: Path) -> Tuple[bool, str]:
        """Backup Minecraft world files"""
        try:
            world_backup_dir = backup_path / "worlds"
            world_backup_dir.mkdir(exist_ok=True)
            
            minecraft_dir = Path("minecraft_server")
            if not minecraft_dir.exists():
                return False, "Minecraft server directory not found"
            
            # Find world directories
            world_dirs = []
            for item in minecraft_dir.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    # Check if it's a world directory
                    if (item / 'level.dat').exists() or (item / 'region').exists():
                        world_dirs.append(item)
            
            if not world_dirs:
                return False, "No world directories found"
            
            # Backup each world
            for world_dir in world_dirs:
                world_name = world_dir.name
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                
                if self.config.compress_backups:
                    # Create compressed archive
                    archive_path = world_backup_dir / f"{world_name}_{timestamp}.tar.gz"
                    with tarfile.open(archive_path, 'w:gz') as tar:
                        tar.add(world_dir, arcname=world_name)
                else:
                    # Copy directory
                    dest_dir = world_backup_dir / f"{world_name}_{timestamp}"
                    shutil.copytree(world_dir, dest_dir)
            
            logger.info(f"World backup completed: {len(world_dirs)} worlds")
            return True, f"Worlds backed up: {', '.join(w.name for w in world_dirs)}"
            
        except Exception as e:
            logger.error(f"World backup failed: {e}")
            return False, f"World backup error: {str(e)}"
    
    def _backup_logs(self, backup_path: Path) -> Tuple[bool, str]:
        """Backup log files"""
        try:
            log_backup_dir = backup_path / "logs"
            log_backup_dir.mkdir(exist_ok=True)
            
            log_sources = [
                Path("logs"),
                Path("minecraft_server/logs")
            ]
            
            backed_up = []
            for log_source in log_sources:
                if log_source.exists() and log_source.is_dir():
                    dest_name = f"{log_source.name}_backup"
                    shutil.copytree(log_source, log_backup_dir / dest_name, dirs_exist_ok=True)
                    backed_up.append(str(log_source))
            
            logger.info(f"Log backup completed: {len(backed_up)} directories")
            return True, f"Logs backed up: {', '.join(backed_up)}"
            
        except Exception as e:
            logger.error(f"Log backup failed: {e}")
            return False, f"Log backup error: {str(e)}"
    
    def _compress_backup(self, backup_path: Path):
        """Compress backup directory"""
        try:
            archive_path = backup_path.with_suffix('.tar.gz')
            with tarfile.open(archive_path, 'w:gz') as tar:
                tar.add(backup_path, arcname=backup_path.name)
            
            # Remove original directory
            shutil.rmtree(backup_path)
            
            logger.info(f"Backup compressed: {archive_path}")
            
        except Exception as e:
            logger.error(f"Backup compression failed: {e}")
    
    def cleanup_old_backups(self):
        """Clean up old backup files"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
            
            for backup_type in ['database', 'configs', 'worlds', 'full']:
                backup_subdir = self.backup_dir / backup_type
                if not backup_subdir.exists():
                    continue
                
                # Get all backup files/directories
                items = list(backup_subdir.iterdir())
                
                # Sort by modification time (oldest first)
                items.sort(key=lambda x: x.stat().st_mtime)
                
                # Remove old items
                removed = 0
                for item in items:
                    item_date = datetime.fromtimestamp(item.stat().st_mtime)
                    
                    if item_date < cutoff_date:
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                        removed += 1
                
                # Keep only max_backups most recent
                remaining_items = [item for item in items if item.exists()]
                remaining_items.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                if len(remaining_items) > self.config.max_backups:
                    for item in remaining_items[self.config.max_backups:]:
                        if item.is_dir():
                            shutil.rmtree(item)
                        else:
                            item.unlink()
                        removed += 1
                
                if removed > 0:
                    logger.info(f"Cleaned up {removed} old {backup_type} backups")
            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
    
    def list_backups(self) -> Dict[str, List[Dict]]:
        """List all available backups"""
        backups = {}
        
        for backup_type in ['database', 'configs', 'worlds', 'full']:
            backup_subdir = self.backup_dir / backup_type
            if not backup_subdir.exists():
                backups[backup_type] = []
                continue
            
            items = []
            for item in backup_subdir.iterdir():
                stat = item.stat()
                items.append({
                    'name': item.name,
                    'path': str(item),
                    'size': stat.st_size,
                    'created': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'is_compressed': item.suffix in ['.tar.gz', '.zip']
                })
            
            # Sort by creation time (newest first)
            items.sort(key=lambda x: x['created'], reverse=True)
            backups[backup_type] = items
        
        return backups
    
    def restore_backup(self, backup_type: str, backup_name: str) -> Tuple[bool, str]:
        """Restore from a specific backup"""
        try:
            backup_path = self.backup_dir / backup_type / backup_name
            
            if not backup_path.exists():
                return False, f"Backup not found: {backup_name}"
            
            logger.info(f"Starting restore from: {backup_name}")
            
            if backup_type == 'database':
                return self._restore_database(backup_path)
            elif backup_type == 'configs':
                return self._restore_configs(backup_path)
            elif backup_type == 'worlds':
                return self._restore_worlds(backup_path)
            elif backup_type == 'full':
                return self._restore_full(backup_path)
            else:
                return False, f"Unknown backup type: {backup_type}"
                
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False, f"Restore error: {str(e)}"
    
    def _restore_database(self, backup_path: Path) -> Tuple[bool, str]:
        """Restore database from backup"""
        try:
            # Find the database file in backup
            db_file = None
            for item in backup_path.iterdir():
                if item.suffix == '.db':
                    db_file = item
                    break
            
            if not db_file:
                return False, "No database file found in backup"
            
            # Create backup of current database
            current_db = Path("the_originals.db")
            if current_db.exists():
                backup_current = current_db.with_suffix('.db.backup')
                shutil.copy2(current_db, backup_current)
            
            # Restore database
            shutil.copy2(db_file, current_db)
            
            logger.info(f"Database restored from: {db_file}")
            return True, f"Database restored from {db_file.name}"
            
        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False, f"Database restore error: {str(e)}"
    
    def _restore_configs(self, backup_path: Path) -> Tuple[bool, str]:
        """Restore configuration files from backup"""
        try:
            restored_files = []
            
            # Restore individual config files
            for item in backup_path.iterdir():
                if item.is_file() and item.name != 'manifest.json':
                    dest_path = Path(item.name)
                    
                    # Create backup of current file
                    if dest_path.exists():
                        backup_current = dest_path.with_suffix(dest_path.suffix + '.backup')
                        shutil.copy2(dest_path, backup_current)
                    
                    # Restore file
                    shutil.copy2(item, dest_path)
                    restored_files.append(item.name)
            
            logger.info(f"Config restore completed: {len(restored_files)} files")
            return True, f"Configs restored: {', '.join(restored_files)}"
            
        except Exception as e:
            logger.error(f"Config restore failed: {e}")
            return False, f"Config restore error: {str(e)}"
    
    def _restore_worlds(self, backup_path: Path) -> Tuple[bool, str]:
        """Restore world files from backup"""
        try:
            minecraft_dir = Path("minecraft_server")
            minecraft_dir.mkdir(exist_ok=True)
            
            restored_worlds = []
            
            # Handle compressed world backups
            for item in backup_path.iterdir():
                if item.suffix == '.gz' and item.name.endswith('.tar.gz'):
                    # Extract world from archive
                    with tarfile.open(item, 'r:gz') as tar:
                        tar.extractall(minecraft_dir)
                    
                    world_name = item.name.replace('.tar.gz', '').split('_')[0]
                    restored_worlds.append(world_name)
                
                elif item.is_dir():
                    # Copy world directory
                    world_name = item.name.split('_')[0]
                    dest_path = minecraft_dir / world_name
                    
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    
                    shutil.copytree(item, dest_path)
                    restored_worlds.append(world_name)
            
            logger.info(f"World restore completed: {len(restored_worlds)} worlds")
            return True, f"Worlds restored: {', '.join(restored_worlds)}"
            
        except Exception as e:
            logger.error(f"World restore failed: {e}")
            return False, f"World restore error: {str(e)}"
    
    def _restore_full(self, backup_path: Path) -> Tuple[bool, str]:
        """Restore from full backup"""
        try:
            # If it's a compressed backup, extract it first
            if backup_path.suffix == '.gz':
                extract_path = backup_path.parent / backup_path.stem.replace('.tar', '')
                with tarfile.open(backup_path, 'r:gz') as tar:
                    tar.extractall(backup_path.parent)
                backup_path = extract_path
            
            # Read manifest
            manifest_path = backup_path / 'manifest.json'
            if not manifest_path.exists():
                return False, "Invalid backup: manifest not found"
            
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Restore each component
            restored_components = []
            for component in manifest.get('components', []):
                component_type = component['type']
                component_path = backup_path / component_type
                
                if component_path.exists():
                    if component_type == 'database':
                        success, msg = self._restore_database(component_path)
                    elif component_type == 'configs':
                        success, msg = self._restore_configs(component_path)
                    elif component_type == 'worlds':
                        success, msg = self._restore_worlds(component_path)
                    else:
                        continue
                    
                    if success:
                        restored_components.append(component_type)
            
            logger.info(f"Full restore completed: {len(restored_components)} components")
            return True, f"Full restore completed: {', '.join(restored_components)}"
            
        except Exception as e:
            logger.error(f"Full restore failed: {e}")
            return False, f"Full restore error: {str(e)}"
    
    def get_backup_status(self) -> Dict:
        """Get current backup system status"""
        backups = self.list_backups()
        
        # Calculate total backup size
        total_size = 0
        total_count = 0
        
        for backup_type, items in backups.items():
            for item in items:
                total_size += item['size']
                total_count += 1
        
        # Get last backup time
        last_backup = None
        for backup_type, items in backups.items():
            if items:
                backup_time = items[0]['created']  # Most recent
                if not last_backup or backup_time > last_backup:
                    last_backup = backup_time
        
        return {
            'is_running': self.is_running,
            'total_backups': total_count,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'last_backup': last_backup,
            'config': {
                'interval_hours': self.config.backup_interval_hours,
                'max_backups': self.config.max_backups,
                'retention_days': self.config.retention_days,
                'compress_backups': self.config.compress_backups
            },
            'backups_by_type': {
                backup_type: len(items) for backup_type, items in backups.items()
            }
        }

# Global backup manager instance
backup_manager = None

def get_backup_manager() -> BackupManager:
    """Get or create backup manager instance"""
    global backup_manager
    if backup_manager is None:
        backup_manager = BackupManager()
    return backup_manager

def initialize_backup_system():
    """Initialize and start the backup system"""
    manager = get_backup_manager()
    manager.start_scheduler()
    logger.info("Backup system initialized")
    return manager

if __name__ == "__main__":
    # Test the backup system
    config = BackupConfig(
        backup_interval_hours=1,  # Test with 1 hour
        max_backups=5,
        retention_days=7
    )
    
    manager = BackupManager(config)
    
    # Create a test backup
    success, message = manager.create_full_backup()
    print(f"Backup result: {success} - {message}")
    
    # List backups
    backups = manager.list_backups()
    print(f"Available backups: {backups}")
    
    # Show status
    status = manager.get_backup_status()
    print(f"Backup status: {status}") 