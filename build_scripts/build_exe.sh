#!/bin/bash
# ============================================================================
# The Originals - Executable Builder Script (Linux/Mac)
# Creates a standalone executable that you can share with friends!
# ============================================================================

echo ""
echo "========================================"
echo "  THE ORIGINALS - EXECUTABLE BUILDER"
echo "========================================"
echo ""
echo "This script will create a standalone executable"
echo "that your friends can run without installing Python!"
echo ""

# Go to the project root directory (parent of build_scripts)
cd "$(dirname "$0")/.."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.8+ from https://python.org"
    exit 1
fi

echo "✅ Python found"
echo ""

# Check if we're in the right directory
if [ ! -f "app.py" ]; then
    echo "❌ ERROR: app.py not found. Make sure you're running this from the project directory."
    echo "Current directory: $(pwd)"
    echo ""
    echo "Please make sure you have:"
    echo "- app.py"
    echo "- requirements.txt"
    echo "- templates folder"
    echo "- static folder"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "❌ ERROR: requirements.txt not found"
    echo "Current directory: $(pwd)"
    exit 1
fi

echo "✅ Project files found"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "📈 Upgrading pip..."
python -m pip install --upgrade pip

# Install/upgrade PyInstaller and dependencies
echo "📚 Installing build dependencies..."
pip install --upgrade pyinstaller

# Install project requirements
echo "📋 Installing project requirements..."
pip install -r requirements.txt

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build dist

echo ""
echo "🔨 Building executable..."
echo "This may take a few minutes..."
echo ""

# Determine the OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    PLATFORM="macOS"
    DATA_SEP=":"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    PLATFORM="Linux"
    DATA_SEP=":"
else
    # Other Unix-like
    PLATFORM="Unix"
    DATA_SEP=":"
fi

echo "Building for $PLATFORM..."

# Build with PyInstaller
pyinstaller \
    --onefile \
    --windowed \
    --name "TheOriginals" \
    --add-data "templates${DATA_SEP}templates" \
    --add-data "static${DATA_SEP}static" \
    --add-data "minecraft_server${DATA_SEP}minecraft_server" \
    --hidden-import "flask" \
    --hidden-import "flask_sqlalchemy" \
    --hidden-import "flask_login" \
    --hidden-import "flask_socketio" \
    --hidden-import "werkzeug" \
    --hidden-import "eventlet" \
    --hidden-import "psutil" \
    --hidden-import "pystray" \
    --hidden-import "PIL" \
    --hidden-import "requests" \
    --hidden-import "paramiko" \
    --hidden-import "bcrypt" \
    --hidden-import "cryptography" \
    --hidden-import "models.user" \
    --hidden-import "models.node" \
    --hidden-import "models.server" \
    --hidden-import "utils.security" \
    --hidden-import "utils.validation" \
    --hidden-import "utils.logging_config" \
    --exclude-module "matplotlib" \
    --exclude-module "numpy" \
    --exclude-module "pandas" \
    --exclude-module "scipy" \
    --exclude-module "IPython" \
    --exclude-module "jupyter" \
    --exclude-module "tkinter" \
    --clean \
    --noconfirm \
    app.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Build failed! Check the error messages above."
    echo ""
    echo "Common solutions:"
    echo "1. Make sure all dependencies are installed: pip install -r requirements.txt"
    echo "2. Try running with sudo (if permissions issue)"
    echo "3. Check that all required files are present"
    echo ""
    exit 1
fi

echo ""
echo "✅ Build completed successfully!"
echo ""

# Create distribution package
echo "📦 Creating distribution package..."
mkdir -p "dist/TheOriginals_Package"

# Copy executable
cp "dist/TheOriginals" "dist/TheOriginals_Package/"

# Make executable
chmod +x "dist/TheOriginals_Package/TheOriginals"

# Copy documentation
[ -f "README.md" ] && cp "README.md" "dist/TheOriginals_Package/"
[ -f "IMPLEMENTATION_SUMMARY.md" ] && cp "IMPLEMENTATION_SUMMARY.md" "dist/TheOriginals_Package/"
[ -f "QUICK_START_EXECUTABLE.md" ] && cp "QUICK_START_EXECUTABLE.md" "dist/TheOriginals_Package/"

# Create setup guide
echo "Creating setup guide..."
cat > "dist/TheOriginals_Package/SETUP_GUIDE.txt" << 'EOF'
THE ORIGINALS - SETUP GUIDE
===========================

Thank you for downloading The Originals!

QUICK START:
1. Open Terminal/Command Prompt
2. Navigate to this folder
3. Run: ./TheOriginals (Linux/Mac)
4. Wait for it to start (may take a moment on first run)
5. Open your web browser to http://localhost:3000
6. Create your admin account
7. Start managing your Minecraft servers!

FEATURES:
✅ Multi-server management
✅ Mod installation from Modrinth  
✅ Public tunnel creation
✅ Performance monitoring
✅ Automatic backups
✅ User management with secure authentication

SYSTEM REQUIREMENTS:
- Linux/macOS
- 4GB RAM recommended
- 1GB disk space
- Internet connection

TROUBLESHOOTING:
- If permission denied, run: chmod +x TheOriginals
- Check firewall isn't blocking the application
- Ensure port 3000 is available
- First startup may take 30-60 seconds

WHAT'S INCLUDED:
✅ Complete security fixes (no more vulnerabilities!)
✅ Professional modular architecture
✅ Comprehensive input validation
✅ Secure authentication system
✅ Path traversal protection
✅ Command injection prevention
✅ Enterprise-grade logging

SUPPORT:
- GitHub: https://github.com/haloj/the-originals
- Documentation: Check README.md and other .md files

Enjoy managing your Minecraft servers safely!
EOF

echo ""
echo "🎉 SUCCESS! Executable package created!"
echo ""
echo "📁 Location: $(pwd)/dist/TheOriginals_Package/"
echo "📦 Files created:"
echo "   - TheOriginals (main executable)"
echo "   - SETUP_GUIDE.txt (instructions for users)"
echo "   - README.md (documentation)"
echo ""
echo "🚀 TO SHARE WITH FRIENDS:"
echo "1. Zip/tar the entire \"TheOriginals_Package\" folder"
echo "2. Share the archive file"
echo "3. They just extract and run ./TheOriginals!"
echo ""
echo "💡 The executable includes everything needed - no Python installation required!"
echo ""

# Open the package folder (if GUI available)
if command -v xdg-open &> /dev/null; then
    xdg-open "dist/TheOriginals_Package"
elif command -v open &> /dev/null; then
    open "dist/TheOriginals_Package"
fi

echo "Press any key to exit..."
read -n 1 