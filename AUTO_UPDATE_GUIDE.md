# The Originals - Auto-Update System Guide

## Overview

The Originals now features a comprehensive auto-update system that provides:
- **Live Notifications**: Real-time update alerts with modern UI
- **Hourly Background Checks**: Automatic checking for new versions every hour
- **Manual Triggers**: Voice/text commands to check for updates instantly
- **Secure Downloads**: Checksum verification for download integrity
- **Progress Tracking**: Real-time download and installation progress
- **Zero-Downtime Updates**: Automatic restart and update application

## Features

### 1. Live Update Notifications

When a new version is available, you'll receive an attractive notification popup featuring:
- **Version Information**: Current and latest version numbers
- **File Size**: Download size information
- **Release Notes**: Summary of what's new
- **Security Indicators**: Special styling for security updates
- **Action Buttons**: Update now, view details, or dismiss

### 2. Automatic Background Checking

The system automatically checks for updates:
- **Every Hour**: Background checks run continuously
- **On Startup**: Checks for updates when the application starts
- **Manual Refresh**: Every 30 minutes during active use

### 3. Manual Update Triggers

You can trigger update checks by typing any of these phrases:
- `"time to update"`
- `"update now"`
- `"check for updates"`
- `"new version"`

Simply type these phrases in:
- Server command input box
- Any text field monitored by the system
- Even in your development environment (Cursor) when working on the project

### 4. Security Features

The update system includes enterprise-grade security:
- **Download Verification**: SHA256 checksum validation
- **Secure Sources**: Updates only from verified GitHub releases
- **Error Handling**: Comprehensive error recovery and logging
- **Backup Creation**: Automatic backup before updates

## How to Use

### Manual Check for Updates

1. **Via UI**: Click your username → "Check for Updates"
2. **Via Command**: Type "check for updates" in any command box
3. **Via Keyboard**: The system monitors all text inputs for trigger phrases

### When Update is Available

1. **Notification Appears**: A modern notification will appear in the top-right corner
2. **Review Details**: Click "Details" to see full release notes
3. **Install Update**: Click "Update Now" to begin installation
4. **Progress Tracking**: Watch real-time download and installation progress
5. **Automatic Restart**: The application will restart automatically

### Update Process

1. **Download**: Secure download with progress tracking
2. **Verification**: Checksum validation ensures file integrity
3. **Backup**: Current version is automatically backed up
4. **Installation**: Files are updated with error recovery
5. **Restart**: Application restarts with new version

## Configuration

### Update Intervals

Default settings:
- **Background Check**: Every 3600 seconds (1 hour)
- **Foreground Check**: Every 1800 seconds (30 minutes)
- **Minimum Interval**: 300 seconds (5 minutes) between checks

### Manual Trigger Keywords

Default trigger phrases:
- `"time to update"`
- `"update now"`
- `"check for updates"`
- `"new version"`

## API Endpoints

For developers or advanced users:

### Check for Updates
```
GET /api/updates/check?force=true
```

### Get Update Status
```
GET /api/updates/status
```

### Manual Trigger
```
POST /api/updates/trigger
Content-Type: application/json
{"text": "time to update"}
```

### Download and Install
```
POST /api/updates/download
```

### Configuration
```
GET /api/updates/config
POST /api/updates/config
```

## WebSocket Events

The system uses WebSocket for real-time communication:

### Client Events
- `check_updates`: Request update check
- `manual_update_trigger`: Send manual trigger

### Server Events
- `update_available`: New version available
- `update_progress`: Download/install progress
- `update_error`: Error during update process
- `update_triggered`: Manual trigger successful

## Troubleshooting

### Update Fails to Download
- Check internet connection
- Verify GitHub is accessible
- Review system logs for errors

### Update Fails to Install
- Ensure no antivirus interference
- Check file permissions
- Verify sufficient disk space

### Manual Triggers Not Working
- Ensure text contains exact trigger phrases
- Check if recent check was performed (5-minute cooldown)
- Verify WebSocket connection

### Notification Not Appearing
- Check if notification was previously dismissed
- Verify JavaScript is enabled
- Clear browser cache if using web interface

## Advanced Features

### For Developers

When working in Cursor or your development environment:
1. Type "time to update this" in any context
2. The system will automatically detect and check for updates
3. Perfect for maintaining development versions

### For System Administrators

The update system provides:
- Comprehensive logging of all update activities
- Error recovery and rollback capabilities
- Configuration management for update intervals
- Security validation and integrity checking

## Security Considerations

- All downloads are verified with SHA256 checksums
- Updates only accepted from verified GitHub releases
- Automatic backup creation before updates
- Secure update script execution with error handling
- Process isolation and cleanup procedures

## Performance Impact

The auto-update system is designed to be lightweight:
- Background checks use minimal resources
- Smart caching prevents unnecessary network requests
- Efficient WebSocket communication
- Optimized download and installation processes

## Future Enhancements

Planned improvements include:
- Automatic rollback on failed updates
- Staged update deployments
- Update scheduling and maintenance windows
- Enhanced notification customization
- Integration with system notifications

---

**Note**: This system ensures your Minecraft server management platform stays up-to-date with the latest features, security patches, and improvements automatically! 