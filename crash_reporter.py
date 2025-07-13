import os
import sys
import json
import traceback
import platform
import psutil
from datetime import datetime
from pathlib import Path

class CrashReporter:
    def __init__(self, app_name="The Originals", version="2.0.0"):
        self.app_name = app_name
        self.version = version
        self.crash_dir = Path("logs") / "crashes"
        self.crash_dir.mkdir(parents=True, exist_ok=True)
        
    def setup_exception_handler(self):
        """Set up global exception handler"""
        sys.excepthook = self.handle_exception
        
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Don't report keyboard interrupts
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
            
        # Generate crash report
        crash_report = self.generate_crash_report(exc_type, exc_value, exc_traceback)
        
        # Save crash report
        crash_file = self.save_crash_report(crash_report)
        
        # Show user-friendly error message
        self.show_crash_dialog(crash_file)
        
        # Call the default handler for cleanup
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        
    def generate_crash_report(self, exc_type, exc_value, exc_traceback):
        """Generate detailed crash report"""
        crash_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return {
            "crash_id": crash_id,
            "timestamp": datetime.now().isoformat(),
            "app_info": {
                "name": self.app_name,
                "version": self.version,
                "python_version": sys.version,
                "platform": platform.platform(),
                "architecture": platform.architecture()[0]
            },
            "system_info": self.get_system_info(),
            "exception": {
                "type": exc_type.__name__,
                "message": str(exc_value),
                "traceback": traceback.format_exception(exc_type, exc_value, exc_traceback)
            },
            "environment": dict(os.environ),
            "running_processes": self.get_running_processes()
        }
    
    def get_system_info(self):
        """Collect system information"""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "os": platform.system(),
                "os_version": platform.version(),
                "cpu_count": psutil.cpu_count(),
                "memory_total": memory.total,
                "memory_available": memory.available,
                "memory_percent": memory.percent,
                "disk_total": disk.total,
                "disk_free": disk.free,
                "disk_percent": (disk.used / disk.total) * 100
            }
        except Exception:
            return {"error": "Could not collect system info"}
    
    def get_running_processes(self):
        """Get list of running processes (filtered for relevant ones)"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    if any(keyword in proc.info['name'].lower() for keyword in 
                          ['python', 'java', 'minecraft', 'originals']):
                        processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return processes[:10]  # Limit to first 10 relevant processes
        except Exception:
            return []
    
    def save_crash_report(self, crash_report):
        """Save crash report to file"""
        crash_file = self.crash_dir / f"crash_{crash_report['crash_id']}.json"
        
        try:
            with open(crash_file, 'w') as f:
                json.dump(crash_report, f, indent=2, default=str)
            return crash_file
        except Exception as e:
            print(f"Failed to save crash report: {e}")
            return None
    
    def show_crash_dialog(self, crash_file):
        """Show user-friendly crash dialog"""
        crash_message = f"""
{self.app_name} has encountered an unexpected error and needs to close.

Crash Report: {crash_file.name if crash_file else 'Not saved'}
Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

What you can do:
1. Restart {self.app_name} - the issue may be temporary
2. Check the crash report in logs/crashes/ for details
3. Report this issue on GitHub if it persists

The crash report contains technical information to help diagnose the problem.
No personal data is collected.
        """
        
        try:
            # Try to show GUI dialog on Windows
            if os.name == 'nt':
                import ctypes
                ctypes.windll.user32.MessageBoxW(
                    0, crash_message, f"{self.app_name} - Unexpected Error", 0x10
                )
            else:
                print(crash_message)
        except Exception:
            print(crash_message)
    
    def create_crash_report_viewer(self):
        """Create a simple crash report viewer"""
        viewer_script = '''@echo off
echo.
echo ==========================================
echo   The Originals - Crash Report Viewer
echo ==========================================
echo.

if not exist "logs\\crashes" (
    echo No crash reports found.
    pause
    exit /b 0
)

echo Recent crash reports:
echo.
dir /b /o:-d "logs\\crashes\\*.json" | head -10

echo.
set /p "report=Enter crash report filename to view (or press Enter to exit): "

if "%report%"=="" exit /b 0

if exist "logs\\crashes\\%report%" (
    type "logs\\crashes\\%report%"
) else (
    echo Crash report not found: %report%
)

echo.
pause
'''
        
        viewer_path = Path("View Crash Reports.bat")
        with open(viewer_path, 'w') as f:
            f.write(viewer_script)
        
        print(f"Crash report viewer created: {viewer_path}")

# Error logging decorator
def log_errors(crash_reporter=None):
    """Decorator to log errors from specific functions"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if crash_reporter:
                    # Log error without crashing
                    error_report = {
                        "timestamp": datetime.now().isoformat(),
                        "function": func.__name__,
                        "error": str(e),
                        "traceback": traceback.format_exc()
                    }
                    
                    log_file = crash_reporter.crash_dir / "errors.log"
                    with open(log_file, 'a') as f:
                        f.write(json.dumps(error_report) + '\n')
                
                # Re-raise the exception
                raise
        return wrapper
    return decorator

# Flask error handlers
def setup_flask_error_handlers(app, crash_reporter):
    """Set up Flask error handlers"""
    
    @app.errorhandler(500)
    def internal_error(error):
        # Log the error
        crash_report = crash_reporter.generate_crash_report(
            type(error.original_exception),
            error.original_exception,
            error.original_exception.__traceback__
        )
        crash_reporter.save_crash_report(crash_report)
        
        return '''
        <div style="text-align: center; padding: 50px; font-family: Arial;">
            <h2>⚠️ Something went wrong!</h2>
            <p>The Originals encountered an unexpected error.</p>
            <p>A crash report has been saved for debugging.</p>
            <a href="/" style="padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">
                Return to Dashboard
            </a>
        </div>
        ''', 500
    
    @app.errorhandler(404)
    def not_found(error):
        return '''
        <div style="text-align: center; padding: 50px; font-family: Arial;">
            <h2>🔍 Page Not Found</h2>
            <p>The page you're looking for doesn't exist.</p>
            <a href="/" style="padding: 10px 20px; background: #007bff; color: white; text-decoration: none; border-radius: 5px;">
                Return to Dashboard
            </a>
        </div>
        ''', 404

# Initialize crash reporter for the application
def setup_crash_reporting(app=None):
    """Set up crash reporting for the application"""
    crash_reporter = CrashReporter()
    
    # Set up global exception handler
    crash_reporter.setup_exception_handler()
    
    # Create crash report viewer
    crash_reporter.create_crash_report_viewer()
    
    # Set up Flask error handlers if app is provided
    if app:
        setup_flask_error_handlers(app, crash_reporter)
    
    print("Crash reporting system initialized")
    return crash_reporter

if __name__ == "__main__":
    # Test crash reporter
    setup_crash_reporting()
    
    # Simulate a crash for testing
    print("Testing crash reporter...")
    raise Exception("This is a test crash for debugging purposes") 