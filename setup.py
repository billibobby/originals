import os
import sys
import shutil
import subprocess
from pathlib import Path

# Application metadata
APP_NAME = "The Originals"
APP_VERSION = "2.0.0"
APP_DESCRIPTION = "Professional Minecraft Server Manager"
APP_AUTHOR = "The Originals Team"
APP_URL = "https://github.com/your-username/the-originals"

def create_installer():
    """Create Windows installer package"""
    print("Creating The Originals Windows Installer...")
    
    # Create dist directory
    dist_dir = Path("dist")
    dist_dir.mkdir(exist_ok=True)
    
    # Create installer directory structure
    installer_dir = dist_dir / "installer"
    installer_dir.mkdir(exist_ok=True)
    
    app_dir = installer_dir / "app"
    app_dir.mkdir(exist_ok=True)
    
    print("Setting up application structure...")
    
    # Copy application files
    files_to_copy = [
        "app.py",
        "requirements.txt",
        "run.bat",
        "setup.bat",
        "static/",
        "templates/",
        "minecraft_server/",
        ".env.example"
    ]
    
    for file_path in files_to_copy:
        src = Path(file_path)
        if src.exists():
            if src.is_file():
                shutil.copy2(src, app_dir / src.name)
            else:
                shutil.copytree(src, app_dir / src.name, dirs_exist_ok=True)
            print(f"[OK] Copied {file_path}")
    
    # Create installer script
    create_installer_script(installer_dir)
    
    # Create uninstaller script
    create_uninstaller_script(installer_dir)
    
    # Create desktop shortcut template
    create_shortcut_template(installer_dir)
    
    # Create version info
    create_version_info(installer_dir)
    
    print("[OK] Windows installer package created in dist/installer/")
    print("[READY] Ready for distribution!")

def create_installer_script(installer_dir):
    """Create Windows batch installer script"""
    installer_script = f'''@echo off
echo.
echo ==========================================
echo   {APP_NAME} v{APP_VERSION} Installer
echo   {APP_DESCRIPTION}
echo ==========================================
echo.

 :: Check for admin rights
 net session >nul 2>&1
 if %errorLevel% == 0 (
     echo [OK] Running as Administrator
 ) else (
     echo [ERROR] Please run as Administrator
     echo Right-click and select "Run as administrator"
     pause
     exit /b 1
 )

:: Set installation directory
 set "INSTALL_DIR=%ProgramFiles%\\{APP_NAME}"
 set "START_MENU_DIR=%ProgramData%\\Microsoft\\Windows\\Start Menu\\Programs\\{APP_NAME}"
 
 echo [INFO] Installing to: %INSTALL_DIR%
 echo.
 
 :: Create installation directory
 if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
 
 :: Copy application files
 echo [COPY] Copying application files...
 xcopy /E /I /Y "app\\*" "%INSTALL_DIR%\\"
 
 :: Create start menu shortcut
 echo [SHORTCUT] Creating start menu shortcuts...
 if not exist "%START_MENU_DIR%" mkdir "%START_MENU_DIR%"
 
 :: Create desktop shortcut
 echo [SHORTCUT] Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\{APP_NAME}.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\run.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = '{APP_DESCRIPTION}'; $Shortcut.Save()"

:: Create start menu shortcut
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%START_MENU_DIR%\\{APP_NAME}.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\run.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Description = '{APP_DESCRIPTION}'; $Shortcut.Save()"

 :: Run initial setup
 echo [SETUP] Running initial setup...
 cd /d "%INSTALL_DIR%"
 call setup.bat
 
 :: Register uninstaller
 echo [REGISTER] Registering uninstaller...
reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" /v "DisplayName" /t REG_SZ /d "{APP_NAME}" /f
reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" /v "DisplayVersion" /t REG_SZ /d "{APP_VERSION}" /f
reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" /v "Publisher" /t REG_SZ /d "{APP_AUTHOR}" /f
reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" /v "UninstallString" /t REG_SZ /d "%INSTALL_DIR%\\uninstall.bat" /f
reg add "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" /v "InstallLocation" /t REG_SZ /d "%INSTALL_DIR%" /f

 echo.
 echo [SUCCESS] Installation completed successfully!
 echo.
 echo [INFO] You can now run {APP_NAME} from:
 echo    - Desktop shortcut
 echo    - Start Menu
 echo    - Or navigate to: %INSTALL_DIR%
 echo.
 echo [LOGIN] Default login credentials:
 echo    Username: admin
 echo    Password: admin123
 echo.
 pause
'''
    
    with open(installer_dir / "install.bat", "w") as f:
        f.write(installer_script)
    
    print("[OK] Created installer script")

def create_uninstaller_script(installer_dir):
    """Create Windows uninstaller script"""
    uninstaller_script = f'''@echo off
echo.
echo ==========================================
echo   {APP_NAME} Uninstaller
echo ==========================================
echo.

set "INSTALL_DIR=%ProgramFiles%\\{APP_NAME}"
set "START_MENU_DIR=%ProgramData%\\Microsoft\\Windows\\Start Menu\\Programs\\{APP_NAME}"

echo Are you sure you want to uninstall {APP_NAME}?
echo This will remove all application files and settings.
echo.
set /p "confirm=Type 'yes' to continue: "

if not "%confirm%"=="yes" (
    echo Uninstallation cancelled.
    pause
    exit /b 0
)

 echo.
 echo [REMOVE] Removing application files...
 
 :: Stop any running instances
 taskkill /f /im python.exe >nul 2>&1
 
 :: Remove shortcuts
 echo [REMOVE] Removing shortcuts...
 del "%USERPROFILE%\\Desktop\\{APP_NAME}.lnk" >nul 2>&1
 if exist "%START_MENU_DIR%" rmdir /s /q "%START_MENU_DIR%" >nul 2>&1
 
 :: Remove application directory
 echo [REMOVE] Removing installation directory...
 if exist "%INSTALL_DIR%" (
     rmdir /s /q "%INSTALL_DIR%"
 )
 
 :: Remove registry entries
 echo [REMOVE] Removing registry entries...
 reg delete "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{APP_NAME}" /f >nul 2>&1
 
 echo.
 echo [SUCCESS] {APP_NAME} has been uninstalled successfully!
echo.
pause
'''
    
    with open(installer_dir / "app" / "uninstall.bat", "w") as f:
        f.write(uninstaller_script)
    
    print("[OK] Created uninstaller script")

def create_shortcut_template(installer_dir):
    """Create application icon and shortcut templates"""
    # Create a simple icon file (you can replace this with actual icon)
    icon_content = '''
# The Originals Application Icon
# This is a placeholder - replace with actual .ico file
# For professional distribution, create a proper icon file
'''
    
    with open(installer_dir / "app" / "icon.txt", "w") as f:
        f.write(icon_content)
    
    print("[OK] Created icon template")

def create_version_info(installer_dir):
    """Create version information file"""
    version_info = {
        "name": APP_NAME,
        "version": APP_VERSION,
        "description": APP_DESCRIPTION,
        "author": APP_AUTHOR,
        "url": APP_URL,
        "build_type": "Professional",
        "platform": "Windows",
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    }
    
    import json
    with open(installer_dir / "app" / "version.json", "w") as f:
        json.dump(version_info, f, indent=2)
    
    print("[OK] Created version info")

def create_portable_version():
    """Create portable version that doesn't require installation"""
    print("[PORTABLE] Creating portable version...")
    
    portable_dir = Path("dist") / "portable"
    portable_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy all necessary files
    files_to_copy = [
        "app.py",
        "requirements.txt",
        "setup.bat", 
        "run.bat",
        "static/",
        "templates/",
        ".env.example"
    ]
    
    for file_path in files_to_copy:
        src = Path(file_path)
        if src.exists():
            if src.is_file():
                shutil.copy2(src, portable_dir / src.name)
            else:
                shutil.copytree(src, portable_dir / src.name, dirs_exist_ok=True)
    
    # Create portable launcher
    portable_launcher = '''@echo off
echo.
echo ==========================================
echo   The Originals v2.0.0 - Portable
echo ==========================================
echo.
echo [START] Starting The Originals Minecraft Server Manager...
echo.

:: Check if setup has been run
if not exist "minecraft_server_env" (
    echo [SETUP] First time setup - Installing dependencies...
    call setup.bat
)

:: Start the application
call run.bat
'''
    
    with open(portable_dir / "Start The Originals.bat", "w") as f:
        f.write(portable_launcher)
    
    # Create README for portable version
    readme_content = '''# The Originals - Portable Version

This is the portable version of The Originals Minecraft Server Manager.

## Quick Start:
1. Double-click "Start The Originals.bat"
2. Wait for setup to complete (first time only)
3. Access the web interface at http://localhost:3000
4. Login with: admin / admin123

## Features:
- No installation required
- Runs from any folder
- Includes all dependencies
- Full server management capabilities

## System Requirements:
- Windows 10/11
- Python 3.8+ (automatically installed)
- 4GB RAM recommended
- Java 17+ (for Minecraft server)

## Support:
For help and updates, visit: https://github.com/your-username/the-originals
'''
    
    with open(portable_dir / "README.txt", "w") as f:
        f.write(readme_content)
    
    print("[OK] Portable version created in dist/portable/")

if __name__ == "__main__":
    print(f"[BUILD] Building {APP_NAME} v{APP_VERSION} Distribution Package")
    print("=" * 60)
    
    try:
        # Create installer package
        create_installer()
        
        # Create portable version
        create_portable_version()
        
        print("\n" + "=" * 60)
        print("[SUCCESS] Distribution packages created:")
        print("[INSTALLER] Installer: dist/installer/")
        print("[PORTABLE] Portable: dist/portable/")
        print("\n[NEXT] Next steps:")
        print("   1. Test the installer on a clean Windows machine")
        print("   2. Create GitHub repository for releases")
        print("   3. Set up auto-update system")
        print("   4. Create professional icon (.ico file)")
        print("   5. Code signing for security (optional)")
        
    except Exception as e:
        print(f"[ERROR] Error creating distribution package: {e}")
        sys.exit(1) 