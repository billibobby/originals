# The Originals v2.0.0
### Professional Minecraft Server Manager

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/your-username/the-originals/releases)
[![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)](https://github.com/your-username/the-originals)
[![License](https://img.shields.io/badge/license-Proprietary-red.svg)](LICENSE)

**The Originals** is a professional, full-featured Minecraft Server Manager designed to make running and managing Minecraft servers effortless. With its modern web interface, multi-computer support, and comprehensive management tools, it's perfect for both casual players and serious server administrators.

![The Originals Screenshot](docs/screenshot.png)

## 🚀 Features

### Core Functionality
- **🎮 Easy Server Management** - Start, stop, and monitor Minecraft servers with one click
- **📊 Real-time Monitoring** - Live server stats, player counts, and performance metrics
- **💬 Server Console** - Full console access with command history and syntax highlighting
- **🔧 Configuration Management** - Easy-to-use interface for all server settings

### Advanced Features
- **🌐 Public Tunnels** - Share your server with friends anywhere using Cloudflare tunnels
- **🖥️ Multi-Computer Support** - Manage servers across multiple computers on your network
- **📦 Mod Management** - Browse, install, and manage mods from Modrinth
- **👥 User Management** - Role-based access control (Admin, Moderator, User)
- **🔄 Auto-Updates** - Automatic updates with one-click installation
- **🎯 System Tray** - Run in background with system tray integration

### Professional Tools
- **📈 Performance Analytics** - Detailed server performance tracking
- **💾 Backup & Restore** - Automated backup system with easy restore
- **🔐 Security Features** - Built-in security with user authentication
- **📱 Mobile Friendly** - Responsive design works on all devices

## 📦 Installation

### Option 1: Installer Package (Recommended)
1. Download `TheOriginals-Installer-v2.0.0.zip` from [Releases](https://github.com/your-username/the-originals/releases)
2. Extract the zip file
3. Run `install.bat` as Administrator
4. Follow the installation wizard
5. Launch from Desktop shortcut or Start Menu

### Option 2: Portable Version
1. Download `TheOriginals-Portable-v2.0.0.zip` from [Releases](https://github.com/your-username/the-originals/releases)
2. Extract to any folder
3. Run `Start The Originals.bat`
4. Complete the first-run setup wizard

## 🔧 System Requirements

### Minimum Requirements
- **OS**: Windows 10/11 (64-bit)
- **RAM**: 2GB available
- **Storage**: 1GB free space
- **Network**: Internet connection for downloads and updates

### Recommended Requirements
- **OS**: Windows 11 (64-bit)
- **RAM**: 4GB+ available
- **CPU**: Multi-core processor
- **Storage**: 5GB+ free space (for Minecraft server files)
- **Java**: Java 17+ (automatically detected/prompted)

## 🎯 Quick Start

### First Launch
1. **Setup Wizard**: On first run, complete the setup wizard to configure your admin account and preferences
2. **Dashboard Access**: Open your browser to `http://localhost:3000`
3. **Login**: Use the credentials you created during setup
4. **Create Server**: Click "Start Server" to set up your first Minecraft server

### Default Credentials (if using auto-setup)
- **Username**: `admin`
- **Password**: `admin123`
- **🔒 Security**: Change these immediately after first login!

## 📚 User Guide

### Managing Your Server
1. **Starting the Server**
   - Click the "Start Server" button in the dashboard
   - Wait for the server to initialize (may take a few minutes first time)
   - Server status will show "Online" when ready

2. **Inviting Friends**
   - Click "Go Public" to create a tunnel
   - Share the provided public URL with friends
   - They can connect directly without port forwarding

3. **Installing Mods**
   - Go to the "Mods" section
   - Search for mods using the Modrinth integration
   - Click "Install" on any mod you want
   - Restart the server to apply changes

### Multi-Computer Setup
1. **Install on Additional Computers**
   - Run the installer on each computer you want to use
   - They will automatically discover each other on the same network

2. **Deploy Servers to Other Computers**
   - Go to "Manage Computers" in the dashboard
   - Click "Deploy" next to any available computer
   - Distribute server load across multiple machines

### User Management (Admin Only)
1. **Creating Users**
   - Go to User dropdown → "User Management"
   - Invite new users with email invitations
   - Assign roles: Admin, Moderator, or User

2. **Managing Permissions**
   - **Admin**: Full access to all features
   - **Moderator**: Server control and configuration
   - **User**: View-only access to server status

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the installation directory to customize settings:

```env
# Server Configuration
SERVER_PORT=3000
SECRET_KEY=your-secret-key-here

# Minecraft Settings
MINECRAFT_VERSION=1.20.1
MAX_PLAYERS=20
SERVER_NAME=My Minecraft Server

# Features
ENABLE_TUNNEL=true
ENABLE_UPDATES=true
ENABLE_TRAY=true
```

### Advanced Configuration
For advanced users, additional settings can be configured in:
- `config/server.properties` - Minecraft server settings
- `config/app.json` - Application-specific settings

## 🚨 Troubleshooting

### Common Issues

**Server Won't Start**
- Ensure Java 17+ is installed
- Check that port 25565 isn't in use
- Verify EULA acceptance in server properties

**Can't Access Dashboard**
- Confirm the application is running
- Check Windows Firewall settings
- Try accessing via `http://127.0.0.1:3000`

**Tunnel Not Working**
- Check internet connection
- Verify Cloudflare tunnel service is available
- Try restarting the tunnel

**Friends Can't Connect**
- Ensure tunnel is active and public URL is shared
- Check friend's Minecraft version compatibility
- Verify server is running and accepting connections

### Support Channels
- **GitHub Issues**: [Report bugs and feature requests](https://github.com/your-username/the-originals/issues)
- **Documentation**: [Wiki and guides](https://github.com/your-username/the-originals/wiki)
- **Community**: [Discord server](https://discord.gg/your-server)

## 🔄 Updates

### Automatic Updates
- Updates are checked automatically every hour
- You'll be notified when new versions are available
- One-click update installation with automatic restart

### Manual Updates
1. Visit the [Releases page](https://github.com/your-username/the-originals/releases)
2. Download the latest installer
3. Run the installer (will update existing installation)

### Update Channels
- **Stable**: Tested releases (recommended)
- **Beta**: Preview features (experimental)

## 🛠️ Development

### Building from Source
```bash
# Clone the repository
git clone https://github.com/your-username/the-originals.git
cd the-originals

# Install dependencies
pip install -r requirements.txt

# Run the application
python app.py
```

### Creating Distribution Packages
```bash
# Build installer and portable packages
python setup.py

# Packages will be created in dist/ folder
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This software is proprietary and licensed for personal use only. Redistribution and commercial use are prohibited without explicit permission.

## 🙏 Acknowledgments

- **Modrinth** - Mod database and API
- **Cloudflare** - Tunnel infrastructure
- **Minecraft Community** - Inspiration and feedback
- **Bootstrap & Font Awesome** - UI components

## 📞 Contact

- **Developer**: [Your Name](mailto:your-email@example.com)
- **Website**: [https://your-website.com](https://your-website.com)
- **GitHub**: [https://github.com/your-username](https://github.com/your-username)

---

<div align="center">
  <strong>Made with ❤️ for the Minecraft community</strong><br>
  <em>The Originals v2.0.0 - Professional Minecraft Server Manager</em>
</div> 