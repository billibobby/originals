import os
import sys
import json
import requests
import subprocess
import tempfile
import zipfile
from pathlib import Path
from datetime import datetime

class AutoUpdater:
    def __init__(self, current_version="2.0.0", github_repo="haloj/the-originals"):
        self.current_version = current_version
        self.github_repo = github_repo
        self.github_api_url = f"https://api.github.com/repos/{github_repo}/releases/latest"
        self.update_check_url = f"https://raw.githubusercontent.com/{github_repo}/main/latest.json"
        
    def check_for_updates(self):
        """Check if a newer version is available"""
        try:
            response = requests.get(self.github_api_url, timeout=10)
            if response.status_code == 200:
                release_data = response.json()
                latest_version = release_data.get('tag_name', '').replace('v', '')
                
                if self.is_newer_version(latest_version, self.current_version):
                    return {
                        'update_available': True,
                        'latest_version': latest_version,
                        'current_version': self.current_version,
                        'download_url': self.get_download_url(release_data),
                        'release_notes': release_data.get('body', ''),
                        'published_at': release_data.get('published_at')
                    }
                else:
                    return {
                        'update_available': False,
                        'current_version': self.current_version,
                        'latest_version': latest_version
                    }
        except Exception as e:
            print(f"Error checking for updates: {e}")
            return {'update_available': False, 'error': str(e)}
    
    def is_newer_version(self, latest, current):
        """Compare version strings to determine if update is needed"""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            
            # Pad shorter version with zeros
            max_length = max(len(latest_parts), len(current_parts))
            latest_parts += [0] * (max_length - len(latest_parts))
            current_parts += [0] * (max_length - len(current_parts))
            
            return latest_parts > current_parts
        except:
            return False
    
    def get_download_url(self, release_data):
        """Get the installer download URL from release data"""
        assets = release_data.get('assets', [])
        for asset in assets:
            if 'Installer' in asset['name'] and asset['name'].endswith('.zip'):
                return asset['browser_download_url']
        return None
    
    def download_update(self, download_url, progress_callback=None):
        """Download the update package"""
        try:
            temp_dir = tempfile.mkdtemp()
            download_path = Path(temp_dir) / "update.zip"
            
            response = requests.get(download_url, stream=True)
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
            
            return str(download_path)
        except Exception as e:
            print(f"Error downloading update: {e}")
            return None
    
    def create_update_script(self, update_path):
        """Create a script to perform the update"""
        script_content = f'''@echo off
echo.
echo ==========================================
echo   The Originals - Auto Update
echo ==========================================
echo.

echo [UPDATE] Stopping The Originals...
taskkill /f /im python.exe >nul 2>&1

echo [UPDATE] Waiting for application to close...
timeout /t 3 /nobreak >nul

echo [UPDATE] Extracting update package...
powershell -Command "Expand-Archive -Path '{update_path}' -DestinationPath 'update_temp' -Force"

echo [UPDATE] Backing up current installation...
if exist "backup" rmdir /s /q "backup"
mkdir "backup"
xcopy /E /I /Y /Q "app.py" "backup\\" >nul 2>&1
xcopy /E /I /Y /Q "static" "backup\\static\\" >nul 2>&1
xcopy /E /I /Y /Q "templates" "backup\\templates\\" >nul 2>&1

echo [UPDATE] Installing update...
xcopy /E /I /Y /Q "update_temp\\*" ".\\" >nul

echo [UPDATE] Cleaning up...
rmdir /s /q "update_temp" >nul 2>&1

echo [UPDATE] Starting The Originals...
start "" cmd /c "run.bat"

echo.
echo [SUCCESS] Update completed successfully!
echo The Originals has been updated and restarted.
echo.
timeout /t 5 /nobreak >nul
del "%~f0" >nul 2>&1
'''
        
        script_path = Path.cwd() / "update.bat"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        return str(script_path)
    
    def apply_update(self, update_path):
        """Apply the downloaded update"""
        try:
            # Create update script
            script_path = self.create_update_script(update_path)
            
            # Run update script
            subprocess.Popen([script_path], shell=True, cwd=Path.cwd())
            
            # Exit current application
            sys.exit(0)
            
        except Exception as e:
            print(f"Error applying update: {e}")
            return False

# Flask routes for update system
def create_update_routes(app, socketio):
    """Add update routes to Flask application"""
    
    updater = AutoUpdater()
    
    @app.route('/api/updates/check')
    def check_updates():
        """API endpoint to check for updates"""
        result = updater.check_for_updates()
        return result
    
    @app.route('/api/updates/download', methods=['POST'])
    def download_update():
        """API endpoint to download and install updates"""
        try:
            # Check for updates first
            update_info = updater.check_for_updates()
            
            if not update_info.get('update_available'):
                return {'success': False, 'message': 'No updates available'}
            
            download_url = update_info.get('download_url')
            if not download_url:
                return {'success': False, 'message': 'Download URL not found'}
            
            # Notify clients that download is starting
            socketio.emit('update_progress', {'status': 'downloading', 'progress': 0})
            
            def progress_callback(progress):
                socketio.emit('update_progress', {
                    'status': 'downloading', 
                    'progress': progress
                })
            
            # Download update
            update_path = updater.download_update(download_url, progress_callback)
            
            if update_path:
                # Notify clients that installation is starting
                socketio.emit('update_progress', {'status': 'installing', 'progress': 100})
                
                # Apply update (this will restart the application)
                updater.apply_update(update_path)
                
                return {'success': True, 'message': 'Update downloaded and installing...'}
            else:
                return {'success': False, 'message': 'Failed to download update'}
                
        except Exception as e:
            return {'success': False, 'message': f'Update failed: {str(e)}'}

# Auto-update checker service
class UpdateService:
    def __init__(self, app, socketio):
        self.app = app
        self.socketio = socketio
        self.updater = AutoUpdater()
        self.check_interval = 3600  # Check every hour
        
    def start_background_checker(self):
        """Start background update checking"""
        import threading
        import time
        
        def check_loop():
            while True:
                try:
                    update_info = self.updater.check_for_updates()
                    if update_info.get('update_available'):
                        # Notify all connected clients about available update
                        self.socketio.emit('update_available', {
                            'version': update_info.get('latest_version'),
                            'download_url': update_info.get('download_url'),
                            'release_notes': update_info.get('release_notes')
                        })
                    time.sleep(self.check_interval)
                except Exception as e:
                    print(f"Background update check error: {e}")
                    time.sleep(self.check_interval)
        
        thread = threading.Thread(target=check_loop, daemon=True)
        thread.start()

# JavaScript client-side update handler
UPDATE_JS = '''
// Auto-update client functionality
socket.on('update_available', function(data) {
    showUpdateNotification(data);
});

socket.on('update_progress', function(data) {
    updateProgressBar(data);
});

function showUpdateNotification(updateInfo) {
    const notification = `
        <div class="alert alert-info alert-dismissible fade show update-notification" role="alert">
            <h6><i class="fas fa-download me-2"></i>Update Available!</h6>
            <p>Version ${updateInfo.version} is now available.</p>
            <div class="d-flex gap-2">
                <button class="btn btn-primary btn-sm" onclick="downloadUpdate()">
                    <i class="fas fa-download me-1"></i>Update Now
                </button>
                <button class="btn btn-outline-secondary btn-sm" onclick="showReleaseNotes('${updateInfo.version}')">
                    <i class="fas fa-file-alt me-1"></i>Release Notes
                </button>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    document.body.insertAdjacentHTML('afterbegin', notification);
}

async function downloadUpdate() {
    if (!confirm('This will restart The Originals to apply the update. Continue?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/updates/download', {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Update is downloading and will install automatically...', 'info');
        } else {
            showNotification('Update failed: ' + result.message, 'error');
        }
    } catch (error) {
        showNotification('Update failed: ' + error.message, 'error');
    }
}

function updateProgressBar(data) {
    // Show progress during download/installation
    if (data.status === 'downloading') {
        showNotification(`Downloading update... ${Math.round(data.progress)}%`, 'info');
    } else if (data.status === 'installing') {
        showNotification('Installing update... The application will restart shortly.', 'info');
    }
}

async function checkForUpdates() {
    try {
        const response = await fetch('/api/updates/check');
        const result = await response.json();
        
        if (result.update_available) {
            showUpdateNotification(result);
        } else {
            showNotification('You are running the latest version!', 'success');
        }
    } catch (error) {
        showNotification('Failed to check for updates', 'error');
    }
}
'''

def get_update_javascript():
    """Return the JavaScript code for client-side update handling"""
    return UPDATE_JS 