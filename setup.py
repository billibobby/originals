"""
Setup script for The Originals - Minecraft Server Management Platform
Supports building standalone executables and installing as Python package
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
from setuptools import setup, find_packages, Command
from setuptools.command.build import build
from setuptools.command.install import install

# Package information
PACKAGE_NAME = "the-originals"
VERSION = "2.1.0"
DESCRIPTION = "Professional Minecraft Server Management Platform"
LONG_DESCRIPTION = """
The Originals is a comprehensive, secure Minecraft server management platform that allows you to:

- Manage multiple Minecraft servers across different computers
- Install and manage mods from Modrinth
- Create public tunnels for easy server sharing
- Monitor server performance and resources
- Automatically backup and update servers
- Control everything through a beautiful web interface

Features:
✅ Multi-node server management
✅ Secure command execution with injection prevention
✅ Modern web interface with real-time updates
✅ Automatic mod installation and management
✅ Public tunnel creation with Cloudflare
✅ Comprehensive logging and monitoring
✅ Role-based user management
✅ Auto-backup and update system
"""

AUTHOR = "The Originals Team"
AUTHOR_EMAIL = "support@theoriginals.dev"
URL = "https://github.com/haloj/the-originals"

# Requirements
INSTALL_REQUIRES = [
    'Flask==2.3.3',
    'Flask-SocketIO==5.3.6',
    'Flask-SQLAlchemy==3.0.5',
    'Flask-Login==0.6.2',
    'Flask-WTF==1.1.1',
    'Flask-Limiter==3.0.1',
    'Werkzeug==2.3.7',
    'bcrypt==4.0.1',
    'requests==2.31.0',
    'python-socketio==5.9.0',
    'psutil==5.9.5',
    'python-nmap==0.7.1',
    'paramiko==3.3.1',
    'python-dotenv==1.0.0',
    'pyyaml==6.0.1',
    'waitress==2.1.2',
    'eventlet==0.33.3',
    'pystray==0.19.5',
    'pillow==10.1.0',
    'cryptography==41.0.7',
]

BUILD_REQUIRES = [
    'pyinstaller>=5.0.0',
    'auto-py-to-exe>=2.30.0',
] + INSTALL_REQUIRES

DEV_REQUIRES = [
    'pytest==7.4.3',
    'pytest-cov==4.1.0',
    'pytest-mock==3.11.1',
    'pytest-flask==1.3.0',
    'bandit==1.7.5',
    'safety==2.3.4',
    'mypy==1.7.1',
    'black==23.11.0',
    'flake8==6.1.0',
    'radon==6.0.1',
] + BUILD_REQUIRES


class BuildExecutableCommand(Command):
    """Custom command to build standalone executable using PyInstaller."""
    
    description = 'Build standalone executable for distribution'
    user_options = [
        ('onefile', None, 'Create a single executable file'),
        ('windowed', None, 'Create windowed application (no console)'),
        ('debug', None, 'Create debug build with console output'),
    ]
    
    def initialize_options(self):
        self.onefile = False
        self.windowed = True
        self.debug = False
    
    def finalize_options(self):
        pass
    
    def run(self):
        """Build the executable using PyInstaller."""
        print("🔨 Building standalone executable...")
        
        # Install build requirements
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '--upgrade'
        ] + BUILD_REQUIRES)
        
        # Prepare build directory
        build_dir = Path('build')
        dist_dir = Path('dist')
        
        # Clean previous builds
        if build_dir.exists():
            shutil.rmtree(build_dir)
        if dist_dir.exists():
            shutil.rmtree(dist_dir)
        
        # PyInstaller command
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
        ]
        
        if self.onefile:
            cmd.append('--onefile')
        else:
            cmd.append('--onedir')
        
        if self.windowed:
            cmd.append('--windowed')
        else:
            cmd.append('--console')
        
        if self.debug:
            cmd.append('--debug=all')
        
        # Add icon if exists
        icon_path = Path('static/favicon.ico')
        if icon_path.exists():
            cmd.extend(['--icon', str(icon_path)])
        
        # Add data files
        cmd.extend([
            '--add-data', 'templates;templates',
            '--add-data', 'static;static',
            '--add-data', 'minecraft_server;minecraft_server',
        ])
        
        # Add cloudflared if exists
        if Path('cloudflared.exe').exists():
            cmd.extend(['--add-binary', 'cloudflared.exe;.'])
        
        # Hidden imports
        hidden_imports = [
            'flask', 'flask_sqlalchemy', 'flask_login', 'flask_socketio',
            'werkzeug', 'eventlet', 'psutil', 'pystray', 'PIL',
            'requests', 'paramiko', 'bcrypt', 'cryptography',
            'models.user', 'models.node', 'models.server',
            'utils.security', 'utils.validation', 'utils.logging_config'
        ]
        
        for imp in hidden_imports:
            cmd.extend(['--hidden-import', imp])
        
        # Main script
        cmd.append('app.py')
        
        # Set name
        cmd.extend(['--name', 'TheOriginals'])
        
        print(f"Running: {' '.join(cmd)}")
        subprocess.check_call(cmd)
        
        print("✅ Executable built successfully!")
        print(f"📁 Output directory: {dist_dir.absolute()}")
        
        # Create distribution package
        self._create_distribution_package()
    
    def _create_distribution_package(self):
        """Create a complete distribution package."""
        print("📦 Creating distribution package...")
        
        package_dir = Path('dist/TheOriginals_Package')
        package_dir.mkdir(exist_ok=True)
        
        # Copy executable
        exe_src = Path('dist/TheOriginals.exe')
        if exe_src.exists():
            shutil.copy2(exe_src, package_dir)
        else:
            # Directory distribution
            exe_dir = Path('dist/TheOriginals')
            if exe_dir.exists():
                shutil.copytree(exe_dir, package_dir / 'TheOriginals', dirs_exist_ok=True)
        
        # Copy additional files
        additional_files = [
            'README.md',
            'LICENSE',
            'IMPLEMENTATION_SUMMARY.md',
        ]
        
        for file in additional_files:
            if Path(file).exists():
                shutil.copy2(file, package_dir)
        
        # Create setup guide
        setup_guide = package_dir / 'SETUP_GUIDE.txt'
        setup_guide.write_text("""
THE ORIGINALS - SETUP GUIDE
===========================

Thank you for downloading The Originals!

QUICK START:
1. Run TheOriginals.exe
2. Open your web browser to http://localhost:3000
3. Create your admin account
4. Start managing your Minecraft servers!

FEATURES:
✅ Multi-server management
✅ Mod installation from Modrinth
✅ Public tunnel creation
✅ Performance monitoring
✅ Automatic backups
✅ User management

SYSTEM REQUIREMENTS:
- Windows 10/11
- 2GB RAM minimum
- 1GB disk space
- Internet connection

TROUBLESHOOTING:
- If the program doesn't start, run as Administrator
- Check Windows Firewall isn't blocking the application
- Ensure port 3000 is available

SUPPORT:
- GitHub: https://github.com/haloj/the-originals
- Documentation: Check README.md

Enjoy managing your Minecraft servers!
        """.strip())
        
        print(f"✅ Distribution package created: {package_dir.absolute()}")


class CleanCommand(Command):
    """Custom command to clean build artifacts."""
    
    description = 'Clean build artifacts'
    user_options = []
    
    def initialize_options(self):
        pass
    
    def finalize_options(self):
        pass
    
    def run(self):
        """Clean build directories."""
        dirs_to_clean = ['build', 'dist', '*.egg-info', '__pycache__', '.pytest_cache']
        
        for pattern in dirs_to_clean:
            for path in Path('.').glob(pattern):
                if path.is_dir():
                    print(f"Removing directory: {path}")
                    shutil.rmtree(path)
                else:
                    print(f"Removing file: {path}")
                    path.unlink()


class TestCommand(Command):
    """Custom command to run tests."""
    
    description = 'Run test suite'
    user_options = [
        ('coverage', None, 'Run with coverage report'),
        ('security', None, 'Run security tests only'),
    ]
    
    def initialize_options(self):
        self.coverage = False
        self.security = False
    
    def finalize_options(self):
        pass
    
    def run(self):
        """Run the test suite."""
        # Install test requirements
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '--upgrade'
        ] + DEV_REQUIRES)
        
        cmd = [sys.executable, '-m', 'pytest']
        
        if self.security:
            cmd.append('tests/test_security.py')
        else:
            cmd.append('tests/')
        
        if self.coverage:
            cmd.extend(['--cov=.', '--cov-report=html', '--cov-report=term'])
        
        cmd.append('-v')
        
        subprocess.check_call(cmd)


# Main setup configuration
setup(
    name=PACKAGE_NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=AUTHOR_EMAIL,
    url=URL,
    packages=find_packages(),
    include_package_data=True,
    package_data={
        '': ['templates/*', 'static/*', '*.md', '*.txt', '*.yaml', '*.yml'],
    },
    install_requires=INSTALL_REQUIRES,
    extras_require={
        'dev': DEV_REQUIRES,
        'build': BUILD_REQUIRES,
    },
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: End Users/Desktop',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Games/Entertainment',
        'Topic :: System :: Systems Administration',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
    ],
    keywords='minecraft server management web gui mods',
    entry_points={
        'console_scripts': [
            'the-originals=app:main',
        ],
    },
    cmdclass={
        'build_exe': BuildExecutableCommand,
        'clean': CleanCommand,
        'test': TestCommand,
    },
    zip_safe=False,
)

# Helper functions for command-line usage
if __name__ == '__main__':
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == 'build_exe':
            print("🚀 Building executable for easy distribution...")
            print("This will create a standalone .exe file that your friends can run!")
        elif command == 'test':
            print("🧪 Running comprehensive test suite...")
        elif command == 'clean':
            print("🧹 Cleaning build artifacts...")
    
    # Run setup
    setup() 