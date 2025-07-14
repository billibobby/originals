import os
import sys
import json
import uuid
import time
import threading
import subprocess
import requests
import zipfile
import shutil
from pathlib import Path
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.security import generate_password_hash, check_password_hash
import psutil
import yaml
from datetime import datetime, timedelta
from dotenv import load_dotenv
import re
import socket
import nmap
import paramiko
from updater import create_update_routes, get_update_javascript
from crash_reporter import setup_crash_reporting

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', str(uuid.uuid4()))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///the_originals.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize rate limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour", "10 per minute"],
    storage_uri="memory://",
    strategy="fixed-window"
)

# Global variables
server_process = None
server_status = "stopped"
server_logs = []
max_log_lines = 1000
tunnel_process = None
tunnel_url = None
tunnel_status = "stopped"
server_stats = {
    'players': [],
    'tps': 20.0,
    'memory_used': 0,
    'memory_max': 0,
    'cpu_usage': 0.0,
    'uptime': 0
}

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, moderator, user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        permissions = {
            'admin': ['server_control', 'user_management', 'node_management', 'config_edit'],
            'moderator': ['server_control', 'config_edit'],
            'user': ['server_view']
        }
        return permission in permissions.get(self.role, [])

class Node(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    hostname = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    port = db.Column(db.Integer, default=3001)
    ssh_port = db.Column(db.Integer, default=22)
    ssh_username = db.Column(db.String(100))
    status = db.Column(db.String(20), default='offline')  # online, offline, connecting
    capabilities = db.Column(db.Text)  # JSON: cpu_cores, ram_gb, disk_gb, etc.
    last_seen = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_master = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'hostname': self.hostname,
            'ip_address': self.ip_address,
            'port': self.port,
            'status': self.status,
            'capabilities': json.loads(self.capabilities) if self.capabilities else {},
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'is_master': self.is_master
        }

class ServerInstance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    node_id = db.Column(db.Integer, db.ForeignKey('node.id'), nullable=True)
    minecraft_version = db.Column(db.String(20), default='1.20.1')
    server_type = db.Column(db.String(50), default='fabric')  # fabric, forge, vanilla
    status = db.Column(db.String(20), default='stopped')
    port = db.Column(db.Integer, default=25565)
    max_players = db.Column(db.Integer, default=20)
    config = db.Column(db.Text)  # JSON configuration
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_started = db.Column(db.DateTime)
    
    node = db.relationship('Node', backref='servers')
    creator = db.relationship('User', backref='created_servers')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Node Management System
class NodeManager:
    def __init__(self):
        self.nodes = {}
        self.master_node = None
        self.current_node = None
        self.discovery_thread = None
        # Don't start discovery automatically - will be started after DB init
    
    def start_discovery(self):
        """Start network discovery for available nodes"""
        if self.discovery_thread and self.discovery_thread.is_alive():
            return
        
        self.discovery_thread = threading.Thread(target=self._discover_nodes, daemon=True)
        self.discovery_thread.start()
    
    def _discover_nodes(self):
        """Discover nodes on the local network"""
        while True:
            try:
                # Get local network range
                try:
                    local_ip = socket.gethostbyname(socket.gethostname())
                except:
                    # Alternative method for Windows
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect(('8.8.8.8', 80))
                    local_ip = s.getsockname()[0]
                    s.close()
                
                network = '.'.join(local_ip.split('.')[:-1]) + '.0/24'
                print(f"🔍 Scanning network {network} for nodes...")
                
                # First, ensure current computer is registered as master node
                self._register_current_node()
                
                # Scan for nodes running The Originals
                nm = nmap.PortScanner()
                nm.scan(network, '3000-3010')
                
                found_nodes = 0
                for host in nm.all_hosts():
                    if nm[host].state() == 'up':
                        for port in nm[host]['tcp']:
                            if nm[host]['tcp'][port]['state'] == 'open':
                                print(f"🔍 Checking {host}:{port} for The Originals...")
                                self._check_node(host, port)
                                found_nodes += 1
                
                print(f"🔍 Network scan complete. Found {found_nodes} potential nodes.")
                time.sleep(30)  # Scan every 30 seconds
            except Exception as e:
                print(f"❌ Node discovery error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(60)  # Wait longer on error
    
    def _register_current_node(self):
        """Register current computer as master node"""
        try:
            with app.app_context():
                # Get local IP address - try different methods for Windows compatibility
                try:
                    # Method 1: Use hostname resolution
                    local_ip = socket.gethostbyname(socket.gethostname())
                except:
                    # Method 2: Connect to external service to get actual IP
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        s.connect(('8.8.8.8', 80))
                        local_ip = s.getsockname()[0]
                        s.close()
                    except:
                        local_ip = '127.0.0.1'  # Fallback
                
                current_port = int(os.environ.get('SERVER_PORT', 3000))
                
                # Check if current node already exists
                current_node = Node.query.filter_by(ip_address=local_ip, port=current_port).first()
                if not current_node:
                    # Get disk usage with Windows compatibility
                    try:
                        if os.name == 'nt':  # Windows
                            # Use current drive
                            disk_usage = psutil.disk_usage('C:')
                        else:
                            disk_usage = psutil.disk_usage('/')
                        disk_gb = round(disk_usage.total / (1024**3), 2)
                    except:
                        disk_gb = 0  # Fallback if disk usage fails
                    
                    current_node = Node(
                        name=f"{socket.gethostname()} (Master)",
                        hostname=socket.gethostname(),
                        ip_address=local_ip,
                        port=current_port,
                        is_master=True,
                        capabilities=json.dumps({
                            'cpu_cores': psutil.cpu_count(),
                            'ram_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                            'disk_gb': disk_gb,
                            'os': os.name
                        })
                    )
                    db.session.add(current_node)
                
                current_node.status = 'online'
                current_node.last_seen = datetime.utcnow()
                current_node.is_master = True
                db.session.commit()
                print(f"✅ Master node registered: {current_node.name} at {current_node.ip_address}:{current_node.port}")
                
                # Emit update to connected clients
                socketio.emit('node_update', current_node.to_dict())
        except Exception as e:
            print(f"❌ Error registering current node: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(5)  # Wait before retrying
    
    def _check_node(self, ip, port):
        """Check if a discovered host is running The Originals"""
        try:
            response = requests.get(f"http://{ip}:{port}/api/node/info", timeout=5)
            if response.status_code == 200:
                node_info = response.json()
                self._update_node(ip, port, node_info)
        except:
            pass  # Not a valid node
    
    def _update_node(self, ip, port, info):
        """Update node information in database"""
        node = Node.query.filter_by(ip_address=ip, port=port).first()
        if not node:
            node = Node(
                name=info.get('name', f"Node-{ip}"),
                hostname=info.get('hostname', ip),
                ip_address=ip,
                port=port,
                capabilities=json.dumps(info.get('capabilities', {}))
            )
            db.session.add(node)
        
        node.status = 'online'
        node.last_seen = datetime.utcnow()
        db.session.commit()
        
        # Emit update to connected clients
        socketio.emit('node_update', node.to_dict())
    
    def deploy_server_to_node(self, node_id, server_config):
        """Deploy a server to a specific node"""
        node = Node.query.get(node_id)
        if not node or node.status != 'online':
            return False, "Node not available"
        
        try:
            response = requests.post(
                f"http://{node.ip_address}:{node.port}/api/server/deploy",
                json=server_config,
                timeout=30
            )
            return response.status_code == 200, response.json().get('message', 'Unknown error')
        except Exception as e:
            return False, f"Deployment failed: {str(e)}"
    
    def get_available_nodes(self):
        """Get list of available nodes"""
        return Node.query.filter_by(status='online').all()

# Initialize node manager
node_manager = NodeManager()

class TunnelManager:
    def __init__(self):
        self.tunnel_process = None
        self.tunnel_url = None
        self.tunnel_status = "stopped"
    
    def is_cloudflared_installed(self):
        """Check if cloudflared is installed"""
        try:
            result = subprocess.run(['cloudflared', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def install_cloudflared(self):
        """Install cloudflared if not present"""
        try:
            if sys.platform.startswith('darwin'):  # macOS
                subprocess.run(['brew', 'install', 'cloudflared'], check=True)
            elif sys.platform.startswith('linux'):  # Linux
                subprocess.run(['curl', '-L', '--output', '/tmp/cloudflared.deb', 
                              'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb'], check=True)
                subprocess.run(['sudo', 'dpkg', '-i', '/tmp/cloudflared.deb'], check=True)
            elif sys.platform.startswith('win'):  # Windows
                # Download and install for Windows
                import urllib.request
                urllib.request.urlretrieve(
                    'https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe',
                    'cloudflared.exe'
                )
            return True
        except Exception as e:
            print(f"Failed to install cloudflared: {e}")
            return False
    
    def start_tunnel(self, port=3000):
        """Start Cloudflare tunnel"""
        global tunnel_process, tunnel_url, tunnel_status
        
        if tunnel_process and tunnel_process.poll() is None:
            return False, "Tunnel already running"
        
        if not self.is_cloudflared_installed():
            print("Installing cloudflared...")
            if not self.install_cloudflared():
                return False, "Failed to install cloudflared"
        
        try:
            # Start cloudflared tunnel
            tunnel_process = subprocess.Popen([
                'cloudflared', 'tunnel', '--url', f'http://localhost:{port}', '--no-autoupdate'
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            
            # Start a thread to monitor output and extract URL
            threading.Thread(target=self._monitor_tunnel_output, daemon=True).start()
            
            # Wait a moment for tunnel to start
            time.sleep(5)
            
            if tunnel_process.poll() is None:  # Still running
                tunnel_status = "running"
                tunnel_url = "https://tunnel-loading.trycloudflare.com"
                return True, f"Tunnel started successfully!"
            else:
                tunnel_status = "stopped"
                return False, "Failed to start tunnel"
                
        except Exception as e:
            tunnel_status = "stopped"
            return False, f"Error starting tunnel: {str(e)}"
    
    def _monitor_tunnel_output(self):
        """Monitor cloudflared output to extract tunnel URL"""
        global tunnel_process, tunnel_url
        
        if not tunnel_process:
            return
        
        try:
            import re
            while tunnel_process and tunnel_process.poll() is None:
                line = tunnel_process.stdout.readline()
                if line:
                    print(f"Cloudflared: {line.strip()}")  # Debug output
                    if 'https://' in line and 'trycloudflare.com' in line:
                        match = re.search(r'https://[a-zA-Z0-9\-]+\.trycloudflare\.com', line)
                        if match:
                            tunnel_url = match.group(0)
                            print(f"Found tunnel URL: {tunnel_url}")
                            break
        except Exception as e:
            print(f"Error monitoring tunnel output: {e}")
    
    def stop_tunnel(self):
        """Stop Cloudflare tunnel"""
        global tunnel_process, tunnel_url, tunnel_status
        
        if not tunnel_process or tunnel_process.poll() is not None:
            tunnel_status = "stopped"
            return False, "No tunnel running"
        
        try:
            tunnel_process.terminate()
            tunnel_process.wait(timeout=10)
            tunnel_process = None
            tunnel_url = None
            tunnel_status = "stopped"
            return True, "Tunnel stopped successfully"
        except Exception as e:
            tunnel_process = None
            tunnel_url = None
            tunnel_status = "stopped"
            return True, "Tunnel stopped (forced)"
    
    def get_tunnel_url(self):
        """Get the current tunnel URL"""
        global tunnel_url
        return tunnel_url or "https://tunnel-loading.trycloudflare.com"
    
    def get_status(self):
        """Get tunnel status"""
        global tunnel_process, tunnel_status, tunnel_url
        
        if tunnel_process and tunnel_process.poll() is None:
            return {
                'status': 'running',
                'url': tunnel_url or "https://tunnel-loading.trycloudflare.com",
                'process_id': tunnel_process.pid if tunnel_process else None
            }
        else:
            tunnel_status = "stopped"
            tunnel_url = None
            return {
                'status': 'stopped',
                'url': None,
                'process_id': None
            }

# Initialize tunnel manager
tunnel_manager = TunnelManager()

class MinecraftServerManager:
    def __init__(self):
        self.server_dir = Path("minecraft_server")
        self.mods_dir = self.server_dir / "mods"
        self.config_file = "server_config.yml"
        self.server_jar = None
        self.server_process = None
        self.server_port = 25565
        self.rcon_port = 25575
        self.ensure_directories()
        self.load_config()
    
    def ensure_directories(self):
        """Create necessary directories"""
        self.server_dir.mkdir(exist_ok=True)
        self.mods_dir.mkdir(exist_ok=True)
        (self.server_dir / "world").mkdir(exist_ok=True)
        (self.server_dir / "config").mkdir(exist_ok=True)
    
    def load_config(self):
        """Load server configuration"""
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
                self.server_port = config.get('server_port', 25565)
                self.rcon_port = config.get('rcon_port', 25575)
    
    def save_config(self):
        """Save server configuration"""
        config = {
            'server_port': self.server_port,
            'rcon_port': self.rcon_port,
            'last_updated': datetime.now().isoformat()
        }
        with open(self.config_file, 'w') as f:
            yaml.dump(config, f)
    
    def download_fabric_server(self, minecraft_version="1.20.1"):
        """Download Fabric server if not exists"""
        fabric_installer_url = "https://maven.fabricmc.net/net/fabricmc/fabric-installer/0.11.2/fabric-installer-0.11.2.jar"
        installer_path = self.server_dir / "fabric-installer.jar"
        
        if not installer_path.exists():
            print("Downloading Fabric installer...")
            response = requests.get(fabric_installer_url)
            with open(installer_path, 'wb') as f:
                f.write(response.content)
        
        # Install Fabric server
        server_jar_path = self.server_dir / "fabric-server-launch.jar"
        if not server_jar_path.exists():
            print("Installing Fabric server...")
            subprocess.run([
                "java", "-jar", str(installer_path), 
                "server", "-dir", str(self.server_dir), 
                "-mcversion", minecraft_version, 
                "-downloadMinecraft"
            ])
        
        self.server_jar = server_jar_path
        return server_jar_path.exists()
    
    def create_server_properties(self):
        """Create server.properties file"""
        properties_path = self.server_dir / "server.properties"
        if not properties_path.exists():
            properties_content = f"""
server-port={self.server_port}
enable-rcon=true
rcon.port={self.rcon_port}
rcon.password=minecraft
online-mode=false
enable-command-block=true
spawn-protection=0
max-players=20
motd=Minecraft Server with Modrinth Mods
difficulty=normal
gamemode=survival
pvp=true
spawn-monsters=true
spawn-animals=true
spawn-npcs=true
generate-structures=true
level-type=default
"""
            with open(properties_path, 'w') as f:
                f.write(properties_content.strip())
    
    def accept_eula(self):
        """Accept Minecraft EULA"""
        eula_path = self.server_dir / "eula.txt"
        with open(eula_path, 'w') as f:
            f.write("eula=true\n")
    
    def start_server(self):
        """Start the Minecraft server"""
        global server_process, server_status
        
        if server_process and server_process.poll() is None:
            return False, "Server is already running"
        
        if not self.server_jar or not self.server_jar.exists():
            if not self.download_fabric_server():
                return False, "Failed to download server"
        
        self.create_server_properties()
        self.accept_eula()
        
        try:
            server_process = subprocess.Popen([
                "java", "-Xmx2G", "-Xms1G", "-jar", str(self.server_jar), "nogui"
            ], cwd=str(self.server_dir), 
               stdout=subprocess.PIPE, 
               stderr=subprocess.PIPE, 
               stdin=subprocess.PIPE,
               text=True, 
               bufsize=1)
            
            server_status = "starting"
            
            # Start log monitoring thread
            threading.Thread(target=self.monitor_server_logs, daemon=True).start()
            
            return True, "Server started successfully"
        except Exception as e:
            return False, f"Failed to start server: {str(e)}"
    
    def stop_server(self):
        """Stop the Minecraft server"""
        global server_process, server_status
        
        if not server_process or server_process.poll() is not None:
            return False, "Server is not running"
        
        try:
            server_process.terminate()
            server_process.wait(timeout=30)
            server_status = "stopped"
            return True, "Server stopped successfully"
        except subprocess.TimeoutExpired:
            server_process.kill()
            server_status = "stopped"
            return True, "Server forcefully stopped"
        except Exception as e:
            return False, f"Failed to stop server: {str(e)}"
    
    def monitor_server_logs(self):
        """Monitor server logs and emit to web interface"""
        global server_logs, server_status, server_stats
        
        while server_process and server_process.poll() is None:
            line = server_process.stdout.readline()
            if line:
                log_entry = {
                    'timestamp': datetime.now().strftime('%H:%M:%S'),
                    'message': line.strip()
                }
                server_logs.append(log_entry)
                
                # Parse server information from logs
                self.parse_log_for_stats(line.strip())
                
                # Keep only last 1000 log lines
                if len(server_logs) > max_log_lines:
                    server_logs = server_logs[-max_log_lines:]
                
                # Emit to web interface
                socketio.emit('server_log', log_entry)
                
                # Check if server is ready
                if "Done" in line and "For help, type" in line:
                    server_status = "running"
                    socketio.emit('server_status', {'status': server_status})
        
        server_status = "stopped"
        socketio.emit('server_status', {'status': server_status})
    
    def parse_log_for_stats(self, log_line):
        """Parse log lines for server statistics"""
        global server_stats
        
        # Parse player join/leave
        if "joined the game" in log_line:
            player_match = re.search(r'(\w+) joined the game', log_line)
            if player_match:
                player_name = player_match.group(1)
                if player_name not in [p['name'] for p in server_stats['players']]:
                    server_stats['players'].append({
                        'name': player_name,
                        'joined': datetime.now().isoformat()
                    })
                    socketio.emit('server_stats', server_stats)
        
        elif "left the game" in log_line:
            player_match = re.search(r'(\w+) left the game', log_line)
            if player_match:
                player_name = player_match.group(1)
                server_stats['players'] = [p for p in server_stats['players'] if p['name'] != player_name]
                socketio.emit('server_stats', server_stats)
        
        # Parse TPS information (if available)
        tps_match = re.search(r'TPS.*?(\d+\.?\d*)', log_line)
        if tps_match:
            server_stats['tps'] = float(tps_match.group(1))
            socketio.emit('server_stats', server_stats)
    
    def get_server_stats(self):
        """Get current server statistics"""
        global server_stats
        
        if server_process and server_process.poll() is None:
            try:
                # Get process information
                process = psutil.Process(server_process.pid)
                memory_info = process.memory_info()
                
                server_stats.update({
                    'memory_used': memory_info.rss // (1024 * 1024),  # MB
                    'cpu_usage': process.cpu_percent(),
                    'uptime': time.time() - process.create_time()
                })
                
                # Get Java heap info if possible
                try:
                    children = process.children(recursive=True)
                    for child in children:
                        if 'java' in child.name().lower():
                            java_memory = child.memory_info()
                            server_stats['memory_used'] = java_memory.rss // (1024 * 1024)
                            server_stats['cpu_usage'] = child.cpu_percent()
                            break
                except:
                    pass
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        return server_stats
    
    def send_server_command(self, command):
        """Send command to running server"""
        if server_process and server_process.poll() is None:
            try:
                server_process.stdin.write(f"{command}\n")
                server_process.stdin.flush()
                return True, f"Command sent: {command}"
            except Exception as e:
                return False, f"Failed to send command: {str(e)}"
        return False, "Server is not running"

    def get_server_config(self):
        """Get current server configuration"""
        properties_path = self.server_dir / "server.properties"
        config = {}
        
        if properties_path.exists():
            try:
                with open(properties_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip()
            except Exception as e:
                print(f"Error reading server config: {e}")
        
        return config
    
    def update_server_config(self, new_config):
        """Update server configuration"""
        properties_path = self.server_dir / "server.properties"
        
        # Read existing config first
        existing_config = self.get_server_config()
        
        # Update with new values
        existing_config.update(new_config)
        
        try:
            with open(properties_path, 'w') as f:
                f.write("# Minecraft server properties\n")
                f.write(f"# Generated by The Originals on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("#\n")
                
                for key, value in existing_config.items():
                    f.write(f"{key}={value}\n")
            
            # Update our internal config
            self.server_port = int(existing_config.get('server-port', 25565))
            self.rcon_port = int(existing_config.get('rcon.port', 25575))
            self.save_config()
            
            return True, "Server configuration updated successfully"
        except Exception as e:
            return False, f"Failed to update server config: {str(e)}"
    
    def get_default_config(self):
        """Get default server configuration template"""
        return {
            'server-port': '25565',
            'enable-rcon': 'true',
            'rcon.port': '25575',
            'rcon.password': 'minecraft',
            'online-mode': 'false',
            'enable-command-block': 'true',
            'spawn-protection': '0',
            'max-players': '20',
            'motd': 'The Originals Minecraft Server',
            'difficulty': 'normal',
            'gamemode': 'survival',
            'pvp': 'true',
            'spawn-monsters': 'true',
            'spawn-animals': 'true',
            'spawn-npcs': 'true',
            'generate-structures': 'true',
            'level-type': 'default',
            'level-name': 'world',
            'view-distance': '10',
            'simulation-distance': '10',
            'enable-whitelist': 'false'
        }

class ModrinthManager:
    def __init__(self, mods_dir):
        self.mods_dir = Path(mods_dir)
        self.api_base = "https://api.modrinth.com/v2"
        self.installed_mods = self.get_installed_mods()
    
    def get_installed_mods(self):
        """Get list of installed mods"""
        mods = []
        for mod_file in self.mods_dir.glob("*.jar"):
            mods.append({
                'filename': mod_file.name,
                'size': mod_file.stat().st_size,
                'modified': datetime.fromtimestamp(mod_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            })
        return mods
    
    def search_mods(self, query, limit=20):
        """Search mods on Modrinth"""
        try:
            response = requests.get(f"{self.api_base}/search", params={
                'query': query,
                'limit': limit,
                'facets': '[["categories:fabric"]]'
            })
            return response.json()
        except Exception as e:
            return {'error': str(e)}
    
    def get_mod_details(self, mod_id):
        """Get detailed information about a mod"""
        try:
            response = requests.get(f"{self.api_base}/project/{mod_id}")
            return response.json()
        except Exception as e:
            return {'error': str(e)}
    
    def get_mod_versions(self, mod_id, minecraft_version="1.20.1"):
        """Get available versions for a mod"""
        try:
            response = requests.get(f"{self.api_base}/project/{mod_id}/version", params={
                'game_versions': [minecraft_version],
                'loaders': ['fabric']
            })
            return response.json()
        except Exception as e:
            return {'error': str(e)}
    
    def download_mod(self, mod_id, version_id=None, minecraft_version="1.20.1"):
        """Download and install a mod"""
        try:
            if not version_id:
                versions = self.get_mod_versions(mod_id, minecraft_version)
                if not versions or 'error' in versions:
                    return False, "No compatible versions found"
                version_id = versions[0]['id']
            
            # Get version details
            response = requests.get(f"{self.api_base}/version/{version_id}")
            version_data = response.json()
            
            # Find the primary file
            primary_file = None
            for file in version_data['files']:
                if file['primary']:
                    primary_file = file
                    break
            
            if not primary_file:
                primary_file = version_data['files'][0]
            
            # Download the mod
            mod_response = requests.get(primary_file['url'])
            mod_path = self.mods_dir / primary_file['filename']
            
            with open(mod_path, 'wb') as f:
                f.write(mod_response.content)
            
            self.installed_mods = self.get_installed_mods()
            return True, f"Successfully installed {primary_file['filename']}"
        
        except Exception as e:
            return False, f"Failed to download mod: {str(e)}"
    
    def remove_mod(self, filename):
        """Remove an installed mod"""
        try:
            mod_path = self.mods_dir / filename
            if mod_path.exists():
                mod_path.unlink()
                self.installed_mods = self.get_installed_mods()
                return True, f"Successfully removed {filename}"
            return False, "Mod file not found"
        except Exception as e:
            return False, f"Failed to remove mod: {str(e)}"

# Initialize managers
server_manager = MinecraftServerManager()
mod_manager = ModrinthManager(server_manager.mods_dir)

# Routes
@app.route('/')
@login_required
def index():
    """Main dashboard"""
    return render_template('index.html')

@app.route('/api/server/status')
@login_required
def get_server_status():
    """Get server status"""
    stats = server_manager.get_server_stats()
    return jsonify({
        'status': server_status,
        'logs': server_logs[-50:],  # Last 50 log entries
        'installed_mods': len(mod_manager.installed_mods),
        'stats': stats
    })

@app.route('/api/server/stats')
@login_required
def get_server_stats():
    """Get detailed server statistics"""
    return jsonify(server_manager.get_server_stats())

@app.route('/api/server/command', methods=['POST'])
@login_required
def send_server_command():
    """Send command to server"""
    if not current_user.has_permission('server_control'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    data = request.json
    command = data.get('command', '').strip()
    
    if not command:
        return jsonify({'success': False, 'message': 'No command provided'})
    
    # Security: Only allow safe commands
    safe_commands = ['list', 'tps', 'help', 'say', 'tell', 'gamemode', 'tp', 'give', 'time']
    command_base = command.split()[0].lower()
    
    if command_base not in safe_commands:
        return jsonify({'success': False, 'message': f'Command "{command_base}" is not allowed'})
    
    success, message = server_manager.send_server_command(command)
    return jsonify({'success': success, 'message': message})

@app.route('/api/server/players')
@login_required
def get_online_players():
    """Get list of online players"""
    return jsonify({
        'players': server_stats['players'],
        'count': len(server_stats['players'])
    })

@app.route('/api/server/start', methods=['POST'])
@login_required
def start_server():
    """Start the server with enhanced error handling"""
    try:
        if not current_user.has_permission('server_control'):
            return jsonify({'success': False, 'message': 'Permission denied'}), 403
        
        # Log the start attempt
        print(f"[SERVER] Start requested by user: {current_user.username}")
        
        success, message = server_manager.start_server()
        
        if success:
            # Update database record if needed
            try:
                with app.app_context():
                    # Could update server instance status here
                    pass
            except Exception as db_error:
                print(f"[WARNING] Database update failed: {db_error}")
                # Don't fail the whole operation for database issues
        
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        error_msg = f"Server start failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return jsonify({'success': False, 'message': error_msg}), 500

@app.route('/api/server/stop', methods=['POST'])
@login_required
def stop_server():
    """Stop the server with enhanced error handling"""
    try:
        if not current_user.has_permission('server_control'):
            return jsonify({'success': False, 'message': 'Permission denied'}), 403
        
        # Log the stop attempt
        print(f"[SERVER] Stop requested by user: {current_user.username}")
        
        success, message = server_manager.stop_server()
        
        if success:
            # Update database record if needed
            try:
                with app.app_context():
                    # Could update server instance status here
                    pass
            except Exception as db_error:
                print(f"[WARNING] Database update failed: {db_error}")
                # Don't fail the whole operation for database issues
        
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        error_msg = f"Server stop failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return jsonify({'success': False, 'message': error_msg}), 500

@app.route('/api/server/config')
@login_required
def get_server_config():
    """Get server configuration"""
    config = server_manager.get_server_config()
    default_config = server_manager.get_default_config()
    
    return jsonify({
        'config': config,
        'default_config': default_config
    })

@app.route('/api/server/config', methods=['POST'])
@login_required
def update_server_config():
    """Update server configuration"""
    if not current_user.has_permission('config_edit'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    data = request.json
    new_config = data.get('config', {})
    
    if not new_config:
        return jsonify({'success': False, 'message': 'No configuration provided'})
    
    success, message = server_manager.update_server_config(new_config)
    return jsonify({'success': success, 'message': message})

@app.route('/api/mods/search')
@login_required
def search_mods():
    """Search for mods"""
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'No search query provided'})
    
    results = mod_manager.search_mods(query)
    return jsonify(results)

@app.route('/api/mods/installed')
@login_required
def get_installed_mods():
    """Get installed mods"""
    return jsonify(mod_manager.installed_mods)

@app.route('/api/mods/install', methods=['POST'])
@login_required
def install_mod():
    """Install a mod"""
    if not current_user.has_permission('server_control'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    data = request.json
    mod_id = data.get('mod_id')
    version_id = data.get('version_id')
    
    if not mod_id:
        return jsonify({'success': False, 'message': 'No mod ID provided'})
    
    success, message = mod_manager.download_mod(mod_id, version_id)
    return jsonify({'success': success, 'message': message})

@app.route('/api/mods/remove', methods=['POST'])
@login_required
def remove_mod():
    """Remove a mod"""
    if not current_user.has_permission('server_control'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    data = request.json
    filename = data.get('filename')
    
    if not filename:
        return jsonify({'success': False, 'message': 'No filename provided'})
    
    success, message = mod_manager.remove_mod(filename)
    return jsonify({'success': success, 'message': message})

@app.route('/share/<share_id>')
def shared_dashboard(share_id):
    """Invitation page for friends to create accounts"""
    # Check if user is already logged in
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Store the invitation code in session for registration
    session['invitation_code'] = share_id
    return render_template('invitation.html', share_id=share_id)

@app.route('/api/share/create', methods=['POST'])
@login_required
def create_share():
    """Create a shareable link"""
    # Allow anyone logged in to create share links
    share_id = str(uuid.uuid4())[:8]
    # In production, store this in a database
    return jsonify({'success': True, 'share_id': share_id, 'url': f'/share/{share_id}'})

# Public Tunnel Routes
@app.route('/api/tunnel/status')
@login_required
def get_tunnel_status():
    """Get tunnel status"""
    status = tunnel_manager.get_status()
    return jsonify(status)

@app.route('/api/tunnel/start', methods=['POST'])
@login_required
def start_tunnel():
    """Start public tunnel"""
    if not current_user.has_permission('server_control'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    port = int(os.environ.get('SERVER_PORT', 3000))
    success, message = tunnel_manager.start_tunnel(port)
    
    if success:
        # Wait a bit for URL to be available
        time.sleep(2)
        status = tunnel_manager.get_status()
        return jsonify({
            'success': True, 
            'message': message,
            'url': status.get('url'),
            'status': status.get('status')
        })
    else:
        return jsonify({'success': False, 'message': message})

@app.route('/api/tunnel/stop', methods=['POST'])
@login_required
def stop_tunnel():
    """Stop public tunnel"""
    if not current_user.has_permission('server_control'):
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    
    success, message = tunnel_manager.stop_tunnel()
    return jsonify({'success': success, 'message': message})

# Authentication Routes
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring systems"""
    try:
        # Check database connection
        with app.app_context():
            db.session.execute('SELECT 1')
            db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    # Check server manager
    try:
        server_manager = MinecraftServerManager()
        server_status = 'initialized'
    except Exception as e:
        server_status = f'error: {str(e)}'
    
    # Check update system
    try:
        from updater import EnhancedAutoUpdater
        updater = EnhancedAutoUpdater()
        update_status = 'active' if updater.is_running else 'inactive'
    except Exception as e:
        update_status = f'error: {str(e)}'
    
    health_data = {
        'status': 'healthy' if db_status == 'healthy' else 'degraded',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '2.0.0',
        'services': {
            'database': db_status,
            'server_manager': server_status,
            'update_system': update_status,
            'web_interface': 'healthy'
        },
        'uptime': {
            'process': psutil.Process().create_time(),
            'formatted': str(datetime.utcnow() - datetime.fromtimestamp(psutil.Process().create_time()))
        }
    }
    
    status_code = 200 if health_data['status'] == 'healthy' else 503
    return jsonify(health_data), status_code

@app.route('/api/health/detailed')
@login_required
def detailed_health_check():
    """Detailed health check for authenticated users"""
    try:
        # System metrics
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('.')
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Database stats
        with app.app_context():
            user_count = User.query.count()
            node_count = Node.query.count()
            server_count = ServerInstance.query.count()
        
        detailed_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'system': {
                'cpu_usage': cpu_percent,
                'memory': {
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent
                },
                'disk': {
                    'total': disk.total,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                }
            },
            'database': {
                'users': user_count,
                'nodes': node_count,
                'servers': server_count
            },
            'features': {
                'auto_updates': True,
                'crash_reporting': True,
                'multi_node': True,
                'tunneling': True
            }
        }
        
        return jsonify(detailed_data)
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(e)
        }), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.json if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            if request.is_json:
                return jsonify({'success': True, 'message': 'Login successful'})
            return redirect(url_for('index'))
        
        if request.is_json:
            return jsonify({'success': False, 'message': 'Invalid username or password'})
        flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Check if this is an invitation registration
    invitation_code = session.get('invitation_code')
    
    if request.method == 'POST':
        data = request.json if request.is_json else request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        display_name = data.get('display_name')
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            if request.is_json:
                return jsonify({'success': False, 'message': 'Username already exists'})
            flash('Username already exists')
            return render_template('register.html', invitation_code=invitation_code)
        
        if User.query.filter_by(email=email).first():
            if request.is_json:
                return jsonify({'success': False, 'message': 'Email already registered'})
            flash('Email already registered')
            return render_template('register.html', invitation_code=invitation_code)
        
        # Determine user role based on invitation or if first user
        if User.query.count() == 0:
            role = 'admin'  # First user is admin
        elif invitation_code:
            role = 'moderator'  # Invited users get moderator privileges
        else:
            role = 'user'  # Regular registration gets user role
        
        # Create new user
        user = User(
            username=username,
            email=email,
            display_name=display_name or username,
            role=role
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Clear invitation code from session
        if invitation_code:
            session.pop('invitation_code', None)
        
        login_user(user)
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Registration successful'})
        return redirect(url_for('index'))
    
    return render_template('register.html', invitation_code=invitation_code)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/api/user/profile')
@login_required
def get_user_profile():
    return jsonify({
        'username': current_user.username,
        'display_name': current_user.display_name,
        'email': current_user.email,
        'role': current_user.role,
        'created_at': current_user.created_at.isoformat(),
        'last_login': current_user.last_login.isoformat() if current_user.last_login else None
    })

@app.route('/api/user/profile', methods=['POST'])
@login_required
def update_user_profile():
    data = request.json
    
    if 'display_name' in data:
        current_user.display_name = data['display_name']
    
    if 'email' in data:
        # Check if email is already taken
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != current_user.id:
            return jsonify({'success': False, 'message': 'Email already in use'})
        current_user.email = data['email']
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Profile updated successfully'})

# Admin User Management Routes
@app.route('/api/admin/users')
@login_required
def get_all_users():
    if not current_user.has_permission('user_management'):
        return jsonify({'error': 'Permission denied'}), 403
    
    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'display_name': user.display_name,
        'email': user.email,
        'role': user.role,
        'is_active': user.is_active,
        'created_at': user.created_at.isoformat() if user.created_at else None,
        'last_login': user.last_login.isoformat() if user.last_login else None
    } for user in users])

@app.route('/api/admin/users/<int:user_id>/role', methods=['POST'])
@login_required
def update_user_role(user_id):
    if not current_user.has_permission('user_management'):
        return jsonify({'error': 'Permission denied'}), 403
    
    user = User.query.get_or_404(user_id)
    data = request.json
    new_role = data.get('role')
    
    if new_role not in ['admin', 'moderator', 'user']:
        return jsonify({'error': 'Invalid role'}), 400
    
    # Prevent removing admin role from last admin
    if user.role == 'admin' and new_role != 'admin':
        admin_count = User.query.filter_by(role='admin').count()
        if admin_count <= 1:
            return jsonify({'error': 'Cannot remove admin role from last admin'}), 400
    
    user.role = new_role
    db.session.commit()
    
    return jsonify({'success': True, 'message': f'User role updated to {new_role}'})

@app.route('/api/admin/users/<int:user_id>/status', methods=['POST'])
@login_required
def update_user_status(user_id):
    if not current_user.has_permission('user_management'):
        return jsonify({'error': 'Permission denied'}), 403
    
    user = User.query.get_or_404(user_id)
    data = request.json
    is_active = data.get('is_active', True)
    
    # Prevent deactivating the last admin
    if user.role == 'admin' and not is_active:
        active_admin_count = User.query.filter_by(role='admin', is_active=True).count()
        if active_admin_count <= 1:
            return jsonify({'error': 'Cannot deactivate the last admin'}), 400
    
    user.is_active = is_active
    db.session.commit()
    
    status = 'activated' if is_active else 'deactivated'
    return jsonify({'success': True, 'message': f'User {status} successfully'})

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if not current_user.has_permission('user_management'):
        return jsonify({'error': 'Permission denied'}), 403
    
    user = User.query.get_or_404(user_id)
    
    # Prevent deleting the last admin
    if user.role == 'admin':
        admin_count = User.query.filter_by(role='admin').count()
        if admin_count <= 1:
            return jsonify({'error': 'Cannot delete the last admin'}), 400
    
    # Prevent users from deleting themselves
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'User deleted successfully'})

# Node Management Routes
@app.route('/api/nodes')
@login_required
def get_nodes():
    if not current_user.has_permission('node_management'):
        return jsonify({'error': 'Permission denied'}), 403
    
    nodes = Node.query.all()
    return jsonify([node.to_dict() for node in nodes])

@app.route('/api/nodes/<int:node_id>/deploy', methods=['POST'])
@login_required
def deploy_to_node(node_id):
    if not current_user.has_permission('server_control'):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.json
    success, message = node_manager.deploy_server_to_node(node_id, data)
    return jsonify({'success': success, 'message': message})

@app.route('/api/nodes/add', methods=['POST'])
@login_required
def add_node_manually():
    if not current_user.has_permission('node_management'):
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.json
    name = data.get('name')
    ip_address = data.get('ip_address')
    port = data.get('port', 3000)
    
    if not name or not ip_address:
        return jsonify({'error': 'Name and IP address are required'}), 400
    
    # Check if node already exists
    existing_node = Node.query.filter_by(ip_address=ip_address, port=port).first()
    if existing_node:
        return jsonify({'error': 'Node with this IP and port already exists'}), 400
    
    # Create new node
    new_node = Node(
        name=name,
        hostname=name,
        ip_address=ip_address,
        port=port,
        status='offline',
        is_master=False,
        capabilities=json.dumps({
            'cpu_cores': 'N/A',
            'ram_gb': 'N/A',
            'disk_gb': 'N/A',
            'os': 'Unknown'
        })
    )
    
    db.session.add(new_node)
    db.session.commit()
    
    # Emit update to connected clients
    socketio.emit('node_update', new_node.to_dict())
    
    return jsonify({'success': True, 'message': 'Node added successfully', 'node': new_node.to_dict()})

@app.route('/api/nodes/<int:node_id>/remove', methods=['DELETE'])
@login_required
def remove_node(node_id):
    if not current_user.has_permission('node_management'):
        return jsonify({'error': 'Permission denied'}), 403
    
    node = Node.query.get_or_404(node_id)
    
    # Prevent removing master node
    if node.is_master:
        return jsonify({'error': 'Cannot remove master node'}), 400
    
    db.session.delete(node)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Node removed successfully'})

@app.route('/api/node/info')
def node_info():
    """Endpoint for node discovery - returns info about this node"""
    try:
        # Get disk usage with Windows compatibility
        try:
            if os.name == 'nt':  # Windows
                disk_usage = psutil.disk_usage('C:')
            else:
                disk_usage = psutil.disk_usage('/')
            disk_gb = round(disk_usage.total / (1024**3), 2)
        except:
            disk_gb = 0  # Fallback if disk usage fails
        
        return jsonify({
            'name': f"The Originals - {socket.gethostname()}",
            'hostname': socket.gethostname(),
            'version': '2.0.0',
            'capabilities': {
                'cpu_cores': psutil.cpu_count(),
                'ram_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'disk_gb': disk_gb,
                'os': os.name
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('server_status', {'status': server_status})

@socketio.on('request_logs')
def handle_request_logs():
    """Send recent logs to client"""
    emit('server_logs', server_logs[-50:])

@socketio.on('request_stats')
def handle_request_stats():
    """Send server stats to client"""
    stats = server_manager.get_server_stats()
    emit('server_stats', stats)

@socketio.on('send_command')
def handle_send_command(data):
    """Handle server command from client"""
    command = data.get('command', '').strip()
    if command:
        success, message = server_manager.send_server_command(command)
        emit('command_result', {'success': success, 'message': message, 'command': command})

if __name__ == '__main__':
    # Initialize enhanced logging system
    from logging_config import setup_logging, log_startup_info
    setup_logging(app)
    
    # Create templates directory and files
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Initialize database
    with app.app_context():
        db.create_all()
        
        # Create default admin user if no users exist
        if User.query.count() == 0:
            admin = User(
                username='admin',
                email='admin@theoriginals.local',
                display_name='Administrator',
                role='admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Created default admin user: admin / admin123")
    
    # Initialize crash reporting system
    crash_reporter = setup_crash_reporting(app)
    
    # Initialize NodeManager after database is ready
    node_manager = NodeManager()
    node_manager.start_discovery()
    
    # Initialize enhanced auto-updater system
    updater = create_update_routes(app, socketio)
    
    port = int(os.environ.get('SERVER_PORT', 3000))
    debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print("Starting The Originals - Minecraft Server Manager v2.0.0...")
    print(f"Access the web interface at: http://localhost:{port}")
    print("Default login: admin / admin123")
    print("Professional features: Auto-updates, Crash reporting, System tray")
    print(f"[UPDATE] Background update checker started (interval: {updater.check_interval}s)")
    print(f"[CONFIG] Debug mode: {'ENABLED' if debug_mode else 'DISABLED'}")
    
    socketio.run(app, host='0.0.0.0', port=port, debug=debug_mode) 