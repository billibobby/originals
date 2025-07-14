import os
import sys
import json
import requests
import subprocess
import tempfile
import zipfile
import hashlib
import threading
import time
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Callable

class EnhancedAutoUpdater:
    def __init__(self, current_version="2.0.0", github_repo="billibobby/originals"):
        self.current_version = current_version
        self.github_repo = github_repo
        self.github_api_url = f"https://api.github.com/repos/{github_repo}/releases/latest"
        self.update_check_url = f"https://raw.githubusercontent.com/{github_repo}/main/version.json"
        self.last_check_time = None
        self.update_callbacks = []
        self.check_interval = 3600  # 1 hour in seconds
        self.background_thread = None
        self.is_running = False
        self.socketio = None
        self.manual_check_keywords = ["time to update", "update now", "check for updates", "new version"]
        
    def set_socketio(self, socketio):
        """Set the SocketIO instance for real-time notifications"""
        self.socketio = socketio
        
    def add_update_callback(self, callback: Callable):
        """Add a callback to be called when updates are available"""
        self.update_callbacks.append(callback)
        
    def remove_update_callback(self, callback: Callable):
        """Remove an update callback"""
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
            
    def notify_update_available(self, update_info: Dict[str, Any]):
        """Notify all callbacks and clients about available updates"""
        # Call registered callbacks
        for callback in self.update_callbacks:
            try:
                callback(update_info)
            except Exception as e:
                print(f"Error in update callback: {e}")
                
        # Notify WebSocket clients
        if self.socketio:
            try:
                self.socketio.emit('update_available', {
                    'version': update_info.get('latest_version'),
                    'current_version': update_info.get('current_version'),
                    'download_url': update_info.get('download_url'),
                    'release_notes': update_info.get('release_notes', '').replace('\n', '<br>'),
                    'published_at': update_info.get('published_at'),
                    'security_update': update_info.get('security_update', False),
                    'file_size': update_info.get('file_size'),
                    'checksum': update_info.get('checksum')
                })
                print(f"[UPDATE] Notified clients about update to version {update_info.get('latest_version')}")
            except Exception as e:
                print(f"Error notifying clients: {e}")
                
    def check_for_updates(self, force_check=False):
        """Check if a newer version is available with enhanced features"""
        try:
            # Check if we should skip this check (unless forced)
            if not force_check and self.last_check_time:
                time_since_last = (datetime.now() - self.last_check_time).total_seconds()
                if time_since_last < 300:  # Don't check more than once every 5 minutes
                    return {'update_available': False, 'message': 'Recent check already performed'}
            
            self.last_check_time = datetime.now()
            
            # Try both GitHub API and direct version check
            update_info = self._check_github_releases()
            if not update_info.get('update_available'):
                update_info = self._check_direct_version()
                
            if update_info.get('update_available'):
                print(f"[UPDATE] New version {update_info.get('latest_version')} available!")
                self.notify_update_available(update_info)
                
            return update_info
            
        except Exception as e:
            error_msg = f"Error checking for updates: {e}"
            print(f"[UPDATE] {error_msg}")
            return {'update_available': False, 'error': error_msg}
    
    def _check_github_releases(self):
        """Check GitHub releases for updates"""
        try:
            response = requests.get(self.github_api_url, timeout=15)
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data.get('tag_name', '').replace('v', '')
                
                if self.is_newer_version(latest_version, self.current_version):
                    download_url, file_size, checksum = self._get_download_info(release_data)
                    
                    return {
                        'update_available': True,
                        'latest_version': latest_version,
                        'current_version': self.current_version,
                        'download_url': download_url,
                        'release_notes': release_data.get('body', ''),
                        'published_at': release_data.get('published_at'),
                        'security_update': 'security' in release_data.get('body', '').lower(),
                        'file_size': file_size,
                        'checksum': checksum,
                        'check_method': 'github_releases'
                    }
                    
            return {'update_available': False, 'current_version': self.current_version}
            
        except Exception as e:
            print(f"GitHub API check failed: {e}")
            return {'update_available': False, 'error': f'GitHub check failed: {e}'}
    
    def _check_direct_version(self):
        """Check direct version endpoint for updates"""
        try:
            response = requests.get(self.update_check_url, timeout=10)
            if response.status_code == 200:
                version_data = response.json()
                latest_version = version_data.get('version', self.current_version)
                
                if self.is_newer_version(latest_version, self.current_version):
                    return {
                        'update_available': True,
                        'latest_version': latest_version,
                        'current_version': self.current_version,
                        'download_url': version_data.get('download_url'),
                        'release_notes': version_data.get('release_notes', ''),
                        'published_at': version_data.get('published_at'),
                        'security_update': version_data.get('security_update', False),
                        'file_size': version_data.get('file_size'),
                        'checksum': version_data.get('checksum'),
                        'check_method': 'direct_version'
                    }
                    
            return {'update_available': False, 'current_version': self.current_version}
            
        except Exception as e:
            print(f"Direct version check failed: {e}")
            return {'update_available': False, 'error': f'Direct check failed: {e}'}
    
    def _get_download_info(self, release_data):
        """Extract download URL, file size, and checksum from release data"""
        assets = release_data.get('assets', [])
        download_url = None
        file_size = None
        checksum = None
        
        for asset in assets:
            if 'Installer' in asset['name'] and asset['name'].endswith('.zip'):
                download_url = asset['browser_download_url']
                file_size = asset.get('size')
                break
                
        # Look for checksum file
        for asset in assets:
            if asset['name'].endswith('.sha256') or asset['name'].endswith('.hash'):
                try:
                    checksum_response = requests.get(asset['browser_download_url'], timeout=10)
                    if checksum_response.status_code == 200:
                        checksum = checksum_response.text.strip()
                        break
                except:
                    pass
                    
        return download_url, file_size, checksum
    
    def is_newer_version(self, latest, current):
        """Enhanced version comparison with better handling"""
        try:
            # Clean version strings
            latest = latest.replace('v', '').strip()
            current = current.replace('v', '').strip()
            
            # Split into parts and convert to integers
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            
            # Normalize to same length
            max_length = max(len(latest_parts), len(current_parts))
            latest_parts += [0] * (max_length - len(latest_parts))
            current_parts += [0] * (max_length - len(current_parts))
            
            return latest_parts > current_parts
            
        except Exception as e:
            print(f"Version comparison error: {e}")
            return False
    
    def verify_download(self, file_path: str, expected_checksum: Optional[str] = None) -> bool:
        """Verify downloaded file integrity"""
        if not expected_checksum:
            return True  # Skip verification if no checksum provided
            
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            calculated_checksum = sha256_hash.hexdigest()
            is_valid = calculated_checksum.lower() == expected_checksum.lower()
            
            if not is_valid:
                print(f"[UPDATE] Checksum mismatch: expected {expected_checksum}, got {calculated_checksum}")
                
            return is_valid
            
        except Exception as e:
            print(f"[UPDATE] Checksum verification failed: {e}")
            return False
    
    def download_update(self, download_url: str, expected_checksum: Optional[str] = None, progress_callback: Optional[Callable] = None):
        """Download update with enhanced progress tracking and verification"""
        try:
            temp_dir = tempfile.mkdtemp()
            download_path = Path(temp_dir) / "update.zip"
            
            print(f"[UPDATE] Downloading update from {download_url}")
            
            response = requests.get(download_url, stream=True)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress)
                            
                        # Notify WebSocket clients
                        if self.socketio:
                            try:
                                self.socketio.emit('update_progress', {
                                    'status': 'downloading',
                                    'progress': progress if total_size > 0 else 0,
                                    'downloaded': downloaded,
                                    'total': total_size
                                })
                            except:
                                pass
            
            print(f"[UPDATE] Download completed: {download_path}")
            
            # Verify download
            if not self.verify_download(str(download_path), expected_checksum):
                raise Exception("Download verification failed")
                
            return str(download_path)
            
        except Exception as e:
            error_msg = f"Download failed: {e}"
            print(f"[UPDATE] {error_msg}")
            if self.socketio:
                try:
                    self.socketio.emit('update_error', {'message': error_msg})
                except:
                    pass
            return None
    
    def create_update_script(self, update_path: str):
        """Create enhanced update script with better error handling"""
        script_content = f'''@echo off
title The Originals - Auto Update System
echo.
echo ==========================================
echo   The Originals - Auto Update v2.0
echo ==========================================
echo.
echo [INFO] Starting update process...
echo [INFO] Update package: {update_path}
echo.

:: Stop all Python processes related to The Originals
echo [UPDATE] Stopping The Originals application...
taskkill /f /im python.exe /fi "WINDOWTITLE eq The Originals*" >nul 2>&1
taskkill /f /im pythonw.exe /fi "WINDOWTITLE eq The Originals*" >nul 2>&1

:: Wait for processes to fully stop
echo [UPDATE] Waiting for processes to stop...
timeout /t 5 /nobreak >nul

:: Create backup with timestamp
echo [UPDATE] Creating backup of current installation...
set "backup_dir=backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%"
set "backup_dir=%backup_dir: =0%"
if exist "%backup_dir%" rmdir /s /q "%backup_dir%"
mkdir "%backup_dir%" >nul 2>&1

:: Backup critical files
xcopy /E /I /Y /Q "*.py" "%backup_dir%\\" >nul 2>&1
xcopy /E /I /Y /Q "static" "%backup_dir%\\static\\" >nul 2>&1
xcopy /E /I /Y /Q "templates" "%backup_dir%\\templates\\" >nul 2>&1
xcopy /E /I /Y /Q "instance" "%backup_dir%\\instance\\" >nul 2>&1
xcopy /E /I /Y /Q "*.txt" "%backup_dir%\\" >nul 2>&1
xcopy /E /I /Y /Q "*.md" "%backup_dir%\\" >nul 2>&1

echo [UPDATE] Extracting update package...
powershell -Command "try {{ Expand-Archive -Path '{update_path}' -DestinationPath 'update_temp' -Force }} catch {{ Write-Host 'Extraction failed:' $_.Exception.Message; exit 1 }}"

if errorlevel 1 (
    echo [ERROR] Failed to extract update package!
    pause
    exit /b 1
)

echo [UPDATE] Installing update files...
xcopy /E /I /Y /Q "update_temp\\*" ".\\" >nul 2>&1

if errorlevel 1 (
    echo [ERROR] Failed to install update files!
    echo [INFO] Attempting to restore from backup...
    xcopy /E /I /Y /Q "%backup_dir%\\*" ".\\" >nul 2>&1
    pause
    exit /b 1
)

echo [UPDATE] Cleaning up temporary files...
rmdir /s /q "update_temp" >nul 2>&1
del "{update_path}" >nul 2>&1

echo [UPDATE] Update completed successfully!
echo [INFO] Backup created in: %backup_dir%
echo.
echo [INFO] Starting The Originals...
timeout /t 2 /nobreak >nul

:: Start the application
if exist "run.bat" (
    start "" cmd /c "run.bat"
) else if exist "app.py" (
    start "" cmd /c "python app.py"
) else (
    echo [ERROR] Could not find startup script!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] The Originals has been updated and restarted!
echo [INFO] Check the application for the new version.
echo.
timeout /t 5 /nobreak >nul

:: Clean up this script
del "%~f0" >nul 2>&1
'''
        
        script_path = Path.cwd() / f"update_{int(time.time())}.bat"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        return str(script_path)
    
    def apply_update(self, update_path: str):
        """Apply the downloaded update with enhanced process management"""
        try:
            print(f"[UPDATE] Applying update from {update_path}")
            
            # Notify clients that installation is starting
            if self.socketio:
                try:
                    self.socketio.emit('update_progress', {
                        'status': 'installing',
                        'progress': 100,
                        'message': 'Installing update... Application will restart shortly.'
                    })
                except:
                    pass
            
            # Create and run update script
            script_path = self.create_update_script(update_path)
            
            # Give clients time to receive the notification
            time.sleep(2)
            
            # Start update script in background
            subprocess.Popen([script_path], shell=True, cwd=Path.cwd())
            
            # Schedule application exit
            threading.Timer(3.0, sys.exit).start()
            
            return True
            
        except Exception as e:
            error_msg = f"Update application failed: {e}"
            print(f"[UPDATE] {error_msg}")
            if self.socketio:
                try:
                    self.socketio.emit('update_error', {'message': error_msg})
                except:
                    pass
            return False
    
    def start_background_checker(self):
        """Start background update checking with enhanced scheduling"""
        if self.background_thread and self.background_thread.is_alive():
            return
            
        self.is_running = True
        self.background_thread = threading.Thread(target=self._background_check_loop, daemon=True)
        self.background_thread.start()
        print(f"[UPDATE] Background update checker started (interval: {self.check_interval}s)")
    
    def stop_background_checker(self):
        """Stop background update checking"""
        self.is_running = False
        if self.background_thread:
            self.background_thread.join(timeout=5)
        print("[UPDATE] Background update checker stopped")
    
    def _background_check_loop(self):
        """Background loop for checking updates"""
        while self.is_running:
            try:
                # Check for updates
                update_info = self.check_for_updates()
                
                if update_info.get('update_available'):
                    print(f"[UPDATE] Background check found update: {update_info.get('latest_version')}")
                    
                # Wait for next check
                for _ in range(self.check_interval):
                    if not self.is_running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                print(f"[UPDATE] Background check error: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def set_check_interval(self, seconds: int):
        """Set the update check interval"""
        self.check_interval = max(300, seconds)  # Minimum 5 minutes
        print(f"[UPDATE] Check interval set to {self.check_interval} seconds")
    
    def check_manual_trigger(self, text: str) -> bool:
        """Check if text contains manual update trigger keywords"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.manual_check_keywords)
    
    def get_update_status(self) -> Dict[str, Any]:
        """Get current update system status"""
        return {
            'current_version': self.current_version,
            'last_check': self.last_check_time.isoformat() if self.last_check_time else None,
            'background_running': self.is_running,
            'check_interval': self.check_interval,
            'manual_keywords': self.manual_check_keywords
        }

# Flask routes for enhanced update system
def create_update_routes(app, socketio):
    """Create enhanced update routes with live notifications"""
    
    updater = EnhancedAutoUpdater()
    updater.set_socketio(socketio)
    
    # Start background checker
    updater.start_background_checker()
    
    @app.route('/api/updates/check')
    def check_updates():
        """API endpoint to check for updates"""
        from flask import request
        force_check = request.args.get('force', 'false').lower() == 'true'
        result = updater.check_for_updates(force_check=force_check)
        return result
    
    @app.route('/api/updates/status')
    def get_update_status():
        """API endpoint to get update system status"""
        return updater.get_update_status()
    
    @app.route('/api/updates/trigger', methods=['POST'])
    def manual_trigger():
        """API endpoint for manual update triggers"""
        from flask import request
        data = request.get_json()
        trigger_text = data.get('text', '')
        
        if updater.check_manual_trigger(trigger_text):
            result = updater.check_for_updates(force_check=True)
            return {'triggered': True, 'result': result}
        else:
            return {'triggered': False, 'message': 'No trigger keywords found'}
    
    @app.route('/api/updates/download', methods=['POST'])
    def download_update():
        """API endpoint to download and install updates"""
        try:
            # Check for updates first
            update_info = updater.check_for_updates(force_check=True)
            
            if not update_info.get('update_available'):
                return {'success': False, 'message': 'No updates available'}
            
            download_url = update_info.get('download_url')
            if not download_url:
                return {'success': False, 'message': 'Download URL not found'}
            
            expected_checksum = update_info.get('checksum')
            
            # Download update
            update_path = updater.download_update(
                download_url, 
                expected_checksum
            )
            
            if update_path:
                # Apply update (this will restart the application)
                if updater.apply_update(update_path):
                    return {'success': True, 'message': 'Update downloaded and installing...'}
                else:
                    return {'success': False, 'message': 'Failed to apply update'}
            else:
                return {'success': False, 'message': 'Failed to download update'}
                
        except Exception as e:
            return {'success': False, 'message': f'Update failed: {str(e)}'}
    
    @app.route('/api/updates/config', methods=['GET', 'POST'])
    def update_config():
        """API endpoint to get/set update configuration"""
        from flask import request
        if request.method == 'GET':
            return {
                'check_interval': updater.check_interval,
                'manual_keywords': updater.manual_check_keywords,
                'background_running': updater.is_running
            }
        else:
            data = request.get_json()
            if 'check_interval' in data:
                updater.set_check_interval(data['check_interval'])
            if 'manual_keywords' in data:
                updater.manual_check_keywords = data['manual_keywords']
            return {'success': True, 'message': 'Configuration updated'}
    
    # Add SocketIO handlers
    @socketio.on('check_updates')
    def handle_check_updates():
        """Handle WebSocket update check requests"""
        result = updater.check_for_updates(force_check=True)
        socketio.emit('update_check_result', result)
    
    @socketio.on('manual_update_trigger')
    def handle_manual_trigger(data):
        """Handle manual update trigger via WebSocket"""
        trigger_text = data.get('text', '')
        if updater.check_manual_trigger(trigger_text):
            result = updater.check_for_updates(force_check=True)
            socketio.emit('update_triggered', {'result': result})
    
    return updater

# Enhanced JavaScript for client-side update handling
def get_update_javascript():
    """Return enhanced JavaScript for update system"""
    return '''
// Enhanced Auto-update client functionality
let updateNotificationShown = false;
let updateCheckInterval = null;

// Socket event handlers
socket.on('update_available', function(data) {
    showUpdateNotification(data);
});

socket.on('update_progress', function(data) {
    updateProgressBar(data);
});

socket.on('update_error', function(data) {
    showNotification('Update failed: ' + data.message, 'error');
});

socket.on('update_check_result', function(data) {
    if (data.update_available) {
        showUpdateNotification(data);
    } else {
        showNotification('You are running the latest version!', 'success');
    }
});

socket.on('update_triggered', function(data) {
    showNotification('Update check triggered!', 'info');
    if (data.result.update_available) {
        showUpdateNotification(data.result);
    }
});

// Enhanced update notification with modern UI
function showUpdateNotification(updateInfo) {
    if (updateNotificationShown) return;
    updateNotificationShown = true;
    
    const isSecurityUpdate = updateInfo.security_update;
    const alertClass = isSecurityUpdate ? 'alert-warning' : 'alert-info';
    const icon = isSecurityUpdate ? 'fas fa-shield-alt' : 'fas fa-download';
    const priority = isSecurityUpdate ? 'SECURITY UPDATE' : 'UPDATE AVAILABLE';
    
    const fileSize = updateInfo.file_size ? formatFileSize(updateInfo.file_size) : 'Unknown size';
    
    const notification = `
        <div class="alert ${alertClass} alert-dismissible fade show update-notification position-fixed" 
             style="top: 20px; right: 20px; z-index: 9999; max-width: 400px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);" 
             role="alert">
            <div class="d-flex align-items-center mb-2">
                <i class="${icon} me-2"></i>
                <strong>${priority}</strong>
            </div>
            <h6 class="mb-1">Version ${updateInfo.version} Available!</h6>
            <small class="text-muted">Current: ${updateInfo.current_version} | Size: ${fileSize}</small>
            
            ${updateInfo.release_notes ? `
                <div class="mt-2 p-2 bg-light rounded">
                    <small>${updateInfo.release_notes.substring(0, 200)}${updateInfo.release_notes.length > 200 ? '...' : ''}</small>
                </div>
            ` : ''}
            
            <div class="d-flex gap-2 mt-3">
                <button class="btn btn-primary btn-sm" onclick="downloadUpdate()" ${isSecurityUpdate ? 'style="background-color: #dc3545; border-color: #dc3545;"' : ''}>
                    <i class="fas fa-download me-1"></i>
                    ${isSecurityUpdate ? 'Install Security Update' : 'Update Now'}
                </button>
                <button class="btn btn-outline-secondary btn-sm" onclick="showReleaseNotes()">
                    <i class="fas fa-file-alt me-1"></i>Details
                </button>
                <button class="btn btn-outline-danger btn-sm" onclick="dismissUpdate()">
                    <i class="fas fa-times me-1"></i>Later
                </button>
            </div>
            
            <div class="progress mt-2 d-none" id="updateProgress">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                     role="progressbar" style="width: 0%"></div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('afterbegin', notification);
    
    // Auto-close after 30 seconds for non-security updates
    if (!isSecurityUpdate) {
        setTimeout(() => {
            dismissUpdate();
        }, 30000);
    }
}

// Enhanced download function with progress
async function downloadUpdate() {
    const notification = document.querySelector('.update-notification');
    const progressBar = notification.querySelector('#updateProgress');
    
    if (!confirm('This will restart The Originals to apply the update. Any unsaved changes will be lost. Continue?')) {
        return;
    }
    
    try {
        // Show progress bar
        progressBar.classList.remove('d-none');
        
        const response = await fetch('/api/updates/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Update is downloading and will install automatically...', 'info');
            
            // Update button states
            const buttons = notification.querySelectorAll('button');
            buttons.forEach(btn => btn.disabled = true);
            
        } else {
            showNotification('Update failed: ' + result.message, 'error');
            progressBar.classList.add('d-none');
        }
    } catch (error) {
        showNotification('Update failed: ' + error.message, 'error');
        progressBar.classList.add('d-none');
    }
}

// Enhanced progress bar updates
function updateProgressBar(data) {
    const progressBar = document.querySelector('#updateProgress .progress-bar');
    const notification = document.querySelector('.update-notification');
    
    if (!progressBar || !notification) return;
    
    const progress = Math.round(data.progress || 0);
    progressBar.style.width = progress + '%';
    progressBar.textContent = progress + '%';
    
    if (data.status === 'downloading') {
        const downloaded = data.downloaded ? formatFileSize(data.downloaded) : '';
        const total = data.total ? formatFileSize(data.total) : '';
        const sizeText = downloaded && total ? ` (${downloaded}/${total})` : '';
        
        notification.querySelector('h6').textContent = `Downloading... ${progress}%${sizeText}`;
        progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-info';
        
    } else if (data.status === 'installing') {
        notification.querySelector('h6').textContent = 'Installing update...';
        progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-success';
        progressBar.style.width = '100%';
        progressBar.textContent = 'Installing...';
        
        // Show countdown
        let countdown = 10;
        const countdownInterval = setInterval(() => {
            if (countdown <= 0) {
                clearInterval(countdownInterval);
                notification.querySelector('h6').textContent = 'Restarting application...';
            } else {
                notification.querySelector('h6').textContent = `Installing... Restarting in ${countdown}s`;
                countdown--;
            }
        }, 1000);
    }
}

// Manual check function
async function checkForUpdates() {
    try {
        showNotification('Checking for updates...', 'info');
        
        const response = await fetch('/api/updates/check?force=true');
        const result = await response.json();
        
        if (result.update_available) {
            showUpdateNotification(result);
        } else {
            showNotification('You are running the latest version!', 'success');
        }
    } catch (error) {
        showNotification('Failed to check for updates: ' + error.message, 'error');
    }
}

// Manual trigger via text input
function handleManualTrigger(text) {
    if (!text) return;
    
    fetch('/api/updates/trigger', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({text: text})
    })
    .then(response => response.json())
    .then(result => {
        if (result.triggered) {
            showNotification('Update check triggered!', 'info');
            if (result.result.update_available) {
                showUpdateNotification(result.result);
            }
        }
    })
    .catch(error => {
        console.error('Manual trigger error:', error);
    });
}

// Dismiss update notification
function dismissUpdate() {
    const notification = document.querySelector('.update-notification');
    if (notification) {
        notification.remove();
        updateNotificationShown = false;
    }
}

// Show release notes
function showReleaseNotes() {
    // Implementation for showing detailed release notes
    alert('Release notes functionality would open a detailed modal here');
}

// Enhanced notification system
function showNotification(message, type = 'info', duration = 5000) {
    const alertClass = {
        'info': 'alert-info',
        'success': 'alert-success',
        'error': 'alert-danger',
        'warning': 'alert-warning'
    }[type] || 'alert-info';
    
    const icon = {
        'info': 'fas fa-info-circle',
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-circle',
        'warning': 'fas fa-exclamation-triangle'
    }[type] || 'fas fa-info-circle';
    
    const notification = document.createElement('div');
    notification.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; left: 20px; z-index: 9998; max-width: 350px;';
    notification.innerHTML = `
        <i class="${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after duration
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, duration);
}

// Initialize update system
document.addEventListener('DOMContentLoaded', function() {
    // Check for updates on page load
    setTimeout(checkForUpdates, 5000);
    
    // Set up periodic checks (every 30 minutes in foreground)
    updateCheckInterval = setInterval(checkForUpdates, 30 * 60 * 1000);
    
    // Listen for manual triggers in command input
    const commandInput = document.querySelector('#commandInput');
    if (commandInput) {
        commandInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                handleManualTrigger(this.value);
            }
        });
    }
    
    // Clean up on page unload
    window.addEventListener('beforeunload', function() {
        if (updateCheckInterval) {
            clearInterval(updateCheckInterval);
        }
    });
});

// Utility function for file size formatting
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}
''' 