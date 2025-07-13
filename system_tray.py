import os
import sys
import threading
import subprocess
import webbrowser
from pathlib import Path

try:
    import pystray
    from PIL import Image
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    print("System tray not available - install pystray and PIL for tray support")

class SystemTrayManager:
    def __init__(self, app_process=None):
        self.app_process = app_process
        self.icon = None
        self.server_running = False
        self.server_port = 3000
        
    def create_icon_image(self):
        """Create a simple icon image for the system tray"""
        try:
            # Try to load existing icon file
            icon_path = Path(__file__).parent / "icon.ico"
            if icon_path.exists():
                return Image.open(icon_path)
        except:
            pass
        
        # Create a simple colored square as fallback
        from PIL import Image, ImageDraw
        
        # Create 64x64 icon
        img = Image.new('RGBA', (64, 64), (102, 126, 234, 255))  # Blue background
        draw = ImageDraw.Draw(img)
        
        # Draw a simple cube-like shape
        # Top face
        draw.polygon([(16, 20), (32, 12), (48, 20), (32, 28)], fill=(140, 160, 240, 255))
        # Left face  
        draw.polygon([(16, 20), (32, 28), (32, 44), (16, 36)], fill=(80, 100, 200, 255))
        # Right face
        draw.polygon([(32, 28), (48, 20), (48, 36), (32, 44)], fill=(60, 80, 180, 255))
        
        return img
    
    def create_menu(self):
        """Create the system tray context menu"""
        if not TRAY_AVAILABLE:
            return None
            
        return pystray.Menu(
            pystray.MenuItem(
                "The Originals v2.0.0",
                self.show_about,
                default=True
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Open Dashboard",
                self.open_dashboard,
                enabled=self.server_running
            ),
            pystray.MenuItem(
                "Start Server" if not self.server_running else "Server Running",
                self.toggle_server,
                enabled=not self.server_running
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Settings",
                self.show_settings
            ),
            pystray.MenuItem(
                "Check for Updates",
                self.check_updates
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(
                "Show Console",
                self.show_console
            ),
            pystray.MenuItem(
                "Exit",
                self.exit_application
            )
        )
    
    def start_tray(self):
        """Start the system tray icon"""
        if not TRAY_AVAILABLE:
            print("System tray integration not available")
            return False
            
        try:
            image = self.create_icon_image()
            menu = self.create_menu()
            
            self.icon = pystray.Icon(
                name="The Originals",
                icon=image,
                title="The Originals - Minecraft Server Manager",
                menu=menu
            )
            
            # Start in a separate thread
            tray_thread = threading.Thread(target=self.icon.run, daemon=True)
            tray_thread.start()
            
            print("System tray icon started")
            return True
            
        except Exception as e:
            print(f"Failed to start system tray: {e}")
            return False
    
    def stop_tray(self):
        """Stop the system tray icon"""
        if self.icon:
            self.icon.stop()
    
    def update_server_status(self, running):
        """Update the server status and refresh menu"""
        self.server_running = running
        if self.icon:
            self.icon.menu = self.create_menu()
    
    def show_notification(self, title, message, timeout=3):
        """Show a system notification"""
        if self.icon and hasattr(self.icon, 'notify'):
            try:
                self.icon.notify(message, title)
            except:
                pass
    
    # Menu action handlers
    def show_about(self, icon=None, item=None):
        """Show about dialog"""
        try:
            webbrowser.open(f"http://localhost:{self.server_port}")
        except:
            pass
    
    def open_dashboard(self, icon=None, item=None):
        """Open the web dashboard"""
        try:
            webbrowser.open(f"http://localhost:{self.server_port}")
        except:
            self.show_notification("Error", "Could not open dashboard")
    
    def toggle_server(self, icon=None, item=None):
        """Start/stop the server"""
        if not self.server_running:
            try:
                # Start the server process
                server_script = Path(__file__).parent / "run.bat"
                if server_script.exists():
                    self.app_process = subprocess.Popen(
                        [str(server_script)], 
                        shell=True,
                        cwd=Path(__file__).parent,
                        creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                    )
                    self.update_server_status(True)
                    self.show_notification("Server Started", "The Originals is now running")
            except Exception as e:
                self.show_notification("Error", f"Failed to start server: {e}")
    
    def show_settings(self, icon=None, item=None):
        """Show settings"""
        try:
            webbrowser.open(f"http://localhost:{self.server_port}#settings")
        except:
            pass
    
    def check_updates(self, icon=None, item=None):
        """Check for updates"""
        try:
            import requests
            response = requests.get("https://api.github.com/repos/your-username/the-originals/releases/latest", timeout=5)
            if response.status_code == 200:
                data = response.json()
                latest_version = data.get('tag_name', '').replace('v', '')
                current_version = "2.0.0"
                
                if latest_version != current_version:
                    self.show_notification("Update Available", f"Version {latest_version} is available!")
                else:
                    self.show_notification("Up to Date", "You have the latest version")
            else:
                self.show_notification("Update Check", "Could not check for updates")
        except Exception as e:
            self.show_notification("Update Check", "Could not check for updates")
    
    def show_console(self, icon=None, item=None):
        """Show/hide console window"""
        if os.name == 'nt':
            try:
                import win32gui
                import win32con
                
                def enum_windows(hwnd, windows):
                    if win32gui.IsWindowVisible(hwnd):
                        window_title = win32gui.GetWindowText(hwnd)
                        if "python" in window_title.lower() or "the originals" in window_title.lower():
                            windows.append(hwnd)
                    return True
                
                windows = []
                win32gui.EnumWindows(enum_windows, windows)
                
                for hwnd in windows:
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    win32gui.SetForegroundWindow(hwnd)
                    break
            except ImportError:
                pass
    
    def exit_application(self, icon=None, item=None):
        """Exit the application"""
        try:
            # Stop the server process
            if self.app_process:
                self.app_process.terminate()
            
            # Stop system tray
            self.stop_tray()
            
            # Kill any remaining Python processes
            if os.name == 'nt':
                os.system('taskkill /f /im python.exe >nul 2>&1')
            
            sys.exit(0)
        except:
            sys.exit(0)

def create_tray_launcher():
    """Create a launcher script that starts the app in system tray mode"""
    launcher_content = '''@echo off
echo Starting The Originals in System Tray mode...

:: Start the application in background
start /B python app.py --tray

:: Start system tray
python system_tray.py

exit
'''
    
    launcher_path = Path(__file__).parent / "Start in Tray.bat"
    with open(launcher_path, 'w') as f:
        f.write(launcher_content)
    
    print(f"Tray launcher created: {launcher_path}")

def main():
    """Main function for standalone tray execution"""
    print("Starting The Originals System Tray...")
    
    tray_manager = SystemTrayManager()
    
    if tray_manager.start_tray():
        print("System tray started. The application will run in the background.")
        print("Right-click the tray icon to access options.")
        
        # Keep the main thread alive
        try:
            while True:
                import time
                time.sleep(1)
        except KeyboardInterrupt:
            print("Shutting down system tray...")
            tray_manager.stop_tray()
    else:
        print("Failed to start system tray")

if __name__ == "__main__":
    main() 