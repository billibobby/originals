# The Originals - Minecraft Server Manager

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/python-3.8+-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/platform-Windows-lightgrey.svg" alt="Platform">
  <img src="https://img.shields.io/badge/license-MIT-orange.svg" alt="License">
</p>

A professional, feature-rich Minecraft server management platform with **live auto-updates**, **real-time notifications**, and **enterprise-grade security**. Built for communities who want a hassle-free server management experience.

## ✨ Features

### 🔄 **Live Auto-Update System**
- **Hourly background checks** for new versions
- **Real-time notifications** with modern UI
- **Manual triggers** via keyword detection
- **Secure SHA256 verification** for all downloads
- **Automatic backups** before updates

### 🎮 **Server Management**
- **One-click server start/stop** with real-time status
- **Live server logs** with WebSocket streaming
- **Player management** and statistics
- **Mod installation** from Modrinth
- **Configuration management** with live editing

### 🌐 **Public Sharing**
- **Cloudflare Tunnels** for instant public access
- **Secure invite system** for friends
- **No port forwarding** required
- **One-click sharing** with automatic URLs

### 👥 **Multi-User Support**
- **Role-based access** (Admin, Moderator, User)
- **User management** with permissions
- **Secure authentication** with account protection
- **Activity logging** and audit trails

### 🖥️ **Multi-Computer Network**
- **Automatic node discovery** on local network
- **Distributed server deployment** across computers
- **Real-time network monitoring**
- **Load balancing** and resource management

## 🚀 Quick Start

### Method 1: Executable (Recommended)
1. Download the latest release from [Releases](https://github.com/billibobby/originals/releases)
2. Run `TheOriginals-Installer.exe`
3. Follow the setup wizard
4. Access at `http://localhost:3000`

### Method 2: From Source
```bash
git clone https://github.com/billibobby/originals.git
cd originals
pip install -r requirements.txt
python app.py
```

## 📱 Live Auto-Update System

The revolutionary auto-update system provides:

### **Automatic Updates**
- Updates check every hour in the background
- Beautiful notifications appear when updates are available
- Zero-effort installation with automatic restart

### **Manual Triggers**
Type any of these phrases anywhere in the application:
- `"time to update"`
- `"update now"`
- `"check for updates"`
- `"new version"`

### **Security Features**
- SHA256 checksum verification
- Automatic backup before updates
- Secure GitHub release downloads
- Error recovery and rollback

## 🎯 How to Use

1. **Start the application** - Auto-update system runs automatically
2. **Default login**: `admin` / `admin123`
3. **Try typing** "time to update" in any command box
4. **Watch for notifications** - they appear automatically every hour
5. **Click "Update Now"** when updates are available

## 🛡️ Security Features

- **Command injection protection** with whitelist validation
- **Path traversal prevention** for file operations
- **Strong password requirements** with account lockout
- **Input validation** and sanitization
- **Secure session management**
- **Comprehensive audit logging**

## 📚 Documentation

- **[Auto-Update Guide](AUTO_UPDATE_GUIDE.md)** - Complete guide to the update system
- **[Build Guide](EASY_BUILD_GUIDE.md)** - How to build executables
- **[Quick Start](QUICK_START_EXECUTABLE.md)** - Get started quickly
- **[Ready to Share](READY_TO_SHARE.md)** - Distribution guide

## 🏗️ Architecture

The application features a modular architecture:
- **`models/`** - Database models with validation
- **`utils/`** - Security, validation, and utility functions
- **`services/`** - Business logic and external integrations
- **`api/`** - REST API endpoints
- **`tests/`** - Comprehensive security test suite

## 🔧 Development

### Requirements
- Python 3.8+
- Flask with SocketIO
- SQLite database
- Modern web browser

### Testing
```bash
python test_update_system.py  # Test auto-update system
python test_all_errors.py     # Security vulnerability tests
```

### Building Executable
```bash
# Windows
run BUILD_EXECUTABLE.bat

# Manual build
python setup.py build_exe
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📊 Project Stats

- **32 files changed** in latest update
- **6,348 insertions** of new code
- **489 deletions** of old code
- **Enterprise-grade security** implementation
- **Professional modular architecture**

## 🎉 What's New in v2.0.0

### ✅ **Major Enhancements**
- **Live auto-update system** with hourly checks
- **Real-time notifications** with modern UI
- **Manual trigger system** via keyword detection
- **Secure download verification** with SHA256
- **Professional executable distribution**

### ✅ **Security Improvements**
- **Complete security audit** and fixes
- **Command injection prevention**
- **Path traversal protection**
- **Strong authentication** with account lockout
- **Comprehensive input validation**

### ✅ **Architecture Overhaul**
- **Modular design** with separate components
- **Enterprise-grade error handling**
- **Professional logging** with rotation
- **Type hints** throughout codebase
- **Comprehensive test suite**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/billibobby/originals/issues)
- **Discussions**: [GitHub Discussions](https://github.com/billibobby/originals/discussions)
- **Updates**: Watch this repository for automatic notifications

## 🙏 Acknowledgments

- Built with Flask and modern web technologies
- Security-focused development practices
- Community-driven feature development
- Professional software engineering standards

---

<p align="center">
  <strong>🎮 Built for Minecraft communities who deserve the best! 🎮</strong>
</p>

<p align="center">
  Made with ❤️ by the community, for the community
</p> 