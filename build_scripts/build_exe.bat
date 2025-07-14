@echo off
REM ============================================================================
REM The Originals - Executable Builder Script
REM Creates a standalone executable that you can share with friends!
REM ============================================================================

echo.
echo ========================================
echo  THE ORIGINALS - EXECUTABLE BUILDER
echo ========================================
echo.
echo This script will create a standalone .exe file
echo that your friends can run without installing Python!
echo.

REM Go to the project root directory (parent of build_scripts)
cd /d "%~dp0\.."

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python found
echo.

REM Check if we're in the right directory
if not exist "app.py" (
    echo ❌ ERROR: app.py not found. Make sure you're running this from the project directory.
    echo Current directory: %cd%
    echo.
    echo Please make sure you have:
    echo - app.py
    echo - requirements.txt
    echo - templates folder
    echo - static folder
    pause
    exit /b 1
)

if not exist "requirements.txt" (
    echo ❌ ERROR: requirements.txt not found
    echo Current directory: %cd%
    pause
    exit /b 1
)

echo ✅ Project files found
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo 📈 Upgrading pip...
python -m pip install --upgrade pip

REM Install/upgrade PyInstaller and dependencies
echo 📚 Installing build dependencies...
pip install --upgrade pyinstaller

REM Install project requirements
echo 📋 Installing project requirements...
pip install -r requirements.txt

REM Clean previous builds
echo 🧹 Cleaning previous builds...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"

echo.
echo 🔨 Building executable...
echo This may take a few minutes...
echo.

REM Build with PyInstaller
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "TheOriginals" ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --add-data "minecraft_server;minecraft_server" ^
    --add-binary "cloudflared.exe;." ^
    --hidden-import "flask" ^
    --hidden-import "flask_sqlalchemy" ^
    --hidden-import "flask_login" ^
    --hidden-import "flask_socketio" ^
    --hidden-import "werkzeug" ^
    --hidden-import "eventlet" ^
    --hidden-import "psutil" ^
    --hidden-import "pystray" ^
    --hidden-import "PIL" ^
    --hidden-import "requests" ^
    --hidden-import "paramiko" ^
    --hidden-import "bcrypt" ^
    --hidden-import "cryptography" ^
    --hidden-import "models.user" ^
    --hidden-import "models.node" ^
    --hidden-import "models.server" ^
    --hidden-import "utils.security" ^
    --hidden-import "utils.validation" ^
    --hidden-import "utils.logging_config" ^
    --exclude-module "matplotlib" ^
    --exclude-module "numpy" ^
    --exclude-module "pandas" ^
    --exclude-module "scipy" ^
    --exclude-module "IPython" ^
    --exclude-module "jupyter" ^
    --exclude-module "tkinter" ^
    --clean ^
    --noconfirm ^
    app.py

if errorlevel 1 (
    echo.
    echo ❌ Build failed! Check the error messages above.
    echo.
    echo Common solutions:
    echo 1. Make sure all dependencies are installed: pip install -r requirements.txt
    echo 2. Try running as Administrator
    echo 3. Check that antivirus isn't blocking PyInstaller
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Build completed successfully!
echo.

REM Create distribution package
echo 📦 Creating distribution package...
if not exist "dist\TheOriginals_Package" mkdir "dist\TheOriginals_Package"

REM Copy executable
copy "dist\TheOriginals.exe" "dist\TheOriginals_Package\"

REM Copy documentation
if exist "README.md" copy "README.md" "dist\TheOriginals_Package\"
if exist "IMPLEMENTATION_SUMMARY.md" copy "IMPLEMENTATION_SUMMARY.md" "dist\TheOriginals_Package\"
if exist "QUICK_START_EXECUTABLE.md" copy "QUICK_START_EXECUTABLE.md" "dist\TheOriginals_Package\"

REM Create setup guide
echo Creating setup guide...
(
echo THE ORIGINALS - SETUP GUIDE
echo ===========================
echo.
echo Thank you for downloading The Originals!
echo.
echo QUICK START:
echo 1. Double-click TheOriginals.exe
echo 2. Wait for it to start ^(may take a moment on first run^)
echo 3. Open your web browser to http://localhost:3000
echo 4. Create your admin account
echo 5. Start managing your Minecraft servers!
echo.
echo FEATURES:
echo ✅ Multi-server management
echo ✅ Mod installation from Modrinth  
echo ✅ Public tunnel creation
echo ✅ Performance monitoring
echo ✅ Automatic backups
echo ✅ User management with secure authentication
echo.
echo SYSTEM REQUIREMENTS:
echo - Windows 10/11
echo - 4GB RAM recommended
echo - 1GB disk space
echo - Internet connection
echo.
echo TROUBLESHOOTING:
echo - If the program doesn't start, try running as Administrator
echo - Check Windows Firewall isn't blocking the application
echo - Ensure port 3000 is available
echo - First startup may take 30-60 seconds
echo.
echo WHAT'S INCLUDED:
echo ✅ Complete security fixes ^(no more vulnerabilities!^)
echo ✅ Professional modular architecture
echo ✅ Comprehensive input validation
echo ✅ Secure authentication system
echo ✅ Path traversal protection
echo ✅ Command injection prevention
echo ✅ Enterprise-grade logging
echo.
echo SUPPORT:
echo - GitHub: https://github.com/haloj/the-originals
echo - Documentation: Check README.md and other .md files
echo.
echo Enjoy managing your Minecraft servers safely!
) > "dist\TheOriginals_Package\SETUP_GUIDE.txt"

echo.
echo 🎉 SUCCESS! Executable package created!
echo.
echo 📁 Location: %cd%\dist\TheOriginals_Package\
echo 📦 Files created:
echo    - TheOriginals.exe ^(main executable^)
echo    - SETUP_GUIDE.txt ^(instructions for users^)
echo    - README.md ^(documentation^)
echo.
echo 🚀 TO SHARE WITH FRIENDS:
echo 1. Zip the entire "TheOriginals_Package" folder
echo 2. Share the zip file
echo 3. They just extract and run TheOriginals.exe!
echo.
echo 💡 The executable includes everything needed - no Python installation required!
echo.

REM Open the package folder
start explorer "dist\TheOriginals_Package"

echo Press any key to exit...
pause >nul 