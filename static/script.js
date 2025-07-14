// Global variables
let socket;
let currentStatus = 'stopped';
let installedMods = [];
let searchResults = [];

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    console.log('The Originals Server Manager v2.0.0 loaded');
    initializeSocket();
    setupEventListeners();
    loadServerStatus();
    loadInstalledMods();
    loadUserProfile();
    loadNodes();
    loadTunnelStatus();
    updateStatusIndicators();
    
    // Update status indicators every 5 seconds
    setInterval(updateStatusIndicators, 5000);
});

// Initialize WebSocket connection
function initializeSocket() {
    socket = io();
    
    socket.on('connect', function() {
        console.log('Connected to server');
        socket.emit('request_logs');
        socket.emit('request_stats');
    });
    
    socket.on('disconnect', function() {
        console.log('Disconnected from server');
        showNotification('Connection lost', 'error');
    });
    
    socket.on('server_status', function(data) {
        updateServerStatus(data.status);
    });
    
    socket.on('server_log', function(data) {
        addLogEntry(data.timestamp, data.message);
    });
    
    socket.on('server_logs', function(logs) {
        displayLogs(logs);
    });
    
    socket.on('server_stats', function(stats) {
        updateServerStats(stats);
    });
    
    socket.on('command_result', function(data) {
        handleCommandResult(data);
    });
    
    socket.on('node_update', function(node) {
        // Refresh nodes display when a node status changes
        loadNodes();
    });
    
    socket.on('user_notification', function(data) {
        showNotification(data.message, data.type || 'info');
    });
}

// Setup event listeners
function setupEventListeners() {
    // Enter key for mod search
    document.getElementById('modSearch').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            searchMods();
        }
    });
    
    // Enter key for server commands
    const serverCommandInput = document.getElementById('serverCommand');
    if (serverCommandInput) {
        serverCommandInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendServerCommand();
            }
        });
    }
    
    // Auto-scroll logs
    const logsContainer = document.getElementById('serverLogs');
    logsContainer.scrollTop = logsContainer.scrollHeight;
}

// Load server status
async function loadServerStatus() {
    try {
        const response = await fetch('/api/server/status');
        const data = await response.json();
        
        updateServerStatus(data.status);
        displayLogs(data.logs);
        document.getElementById('modCount').textContent = data.installed_mods || 0;
        
        if (data.stats) {
            updateServerStats(data.stats);
        }
    } catch (error) {
        console.error('Error loading server status:', error);
        showNotification('Failed to load server status', 'error');
    }
}

// Update server status display
function updateServerStatus(status) {
    currentStatus = status;
    const statusBadge = document.getElementById('serverStatus');
    const statusText = document.getElementById('serverStatusText');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const serverCommand = document.getElementById('serverCommand');
    const sendCommandBtn = document.getElementById('sendCommandBtn');
    
    // Update badge and text
    statusBadge.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    statusText.textContent = status.charAt(0).toUpperCase() + status.slice(1);
    
    // Update badge classes
    statusBadge.className = 'badge ';
    switch(status) {
        case 'running':
            statusBadge.className += 'bg-success';
            startBtn.disabled = true;
            stopBtn.disabled = false;
            serverCommand.disabled = false;
            sendCommandBtn.disabled = false;
            showEnhancedStats(true);
            break;
        case 'starting':
            statusBadge.className += 'bg-warning';
            startBtn.disabled = true;
            stopBtn.disabled = true;
            serverCommand.disabled = true;
            sendCommandBtn.disabled = true;
            showEnhancedStats(false);
            break;
        case 'stopped':
            statusBadge.className += 'bg-secondary';
            startBtn.disabled = false;
            stopBtn.disabled = true;
            serverCommand.disabled = true;
            sendCommandBtn.disabled = true;
            showEnhancedStats(false);
            break;
        default:
            statusBadge.className += 'bg-danger';
            startBtn.disabled = false;
            stopBtn.disabled = true;
            serverCommand.disabled = true;
            sendCommandBtn.disabled = true;
            showEnhancedStats(false);
    }
}

// Show/hide enhanced stats sections
function showEnhancedStats(show) {
    const statsRow = document.getElementById('serverStatsRow');
    const playerListSection = document.getElementById('playerListSection');
    const commandSection = document.getElementById('serverCommandSection');
    
    if (show) {
        statsRow.style.display = 'flex';
        playerListSection.style.display = 'block';
        commandSection.style.display = 'block';
    } else {
        statsRow.style.display = 'none';
        playerListSection.style.display = 'none';
        commandSection.style.display = 'none';
    }
}

// Update server statistics
function updateServerStats(stats) {
    // Update player count
    document.getElementById('playerCount').textContent = stats.players ? stats.players.length : 0;
    document.getElementById('playersOnline').textContent = stats.players ? stats.players.length : 0;
    
    // Update TPS
    document.getElementById('serverTPS').textContent = stats.tps ? stats.tps.toFixed(1) : '20.0';
    
    // Update memory usage
    document.getElementById('memoryUsage').textContent = stats.memory_used ? `${stats.memory_used} MB` : '0 MB';
    
    // Update CPU usage
    document.getElementById('cpuUsage').textContent = stats.cpu_usage ? `${stats.cpu_usage.toFixed(1)}%` : '0%';
    
    // Update player list
    updatePlayerList(stats.players || []);
}

// Update player list display
function updatePlayerList(players) {
    const playerList = document.getElementById('playerList');
    
    if (!players || players.length === 0) {
        playerList.innerHTML = '<div class="text-muted">No players online</div>';
        return;
    }
    
    playerList.innerHTML = players.map(player => `
        <div class="player-item">
            <div class="player-info">
                <strong>${player.name}</strong>
                <small class="text-muted">Joined: ${new Date(player.joined).toLocaleTimeString()}</small>
            </div>
            <div class="player-actions">
                <button class="btn btn-sm btn-outline-primary" onclick="quickCommand('tell ${player.name}')">
                    <i class="fas fa-comment"></i>
                </button>
            </div>
        </div>
    `).join('');
}

// Start server
async function startServer() {
    if (currentStatus !== 'stopped') {
        showNotification('Server is not stopped', 'warning');
        return;
    }
    
    try {
        showNotification('Starting server...', 'info');
        const response = await fetch('/api/server/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Server started successfully', 'success');
            updateServerStatus('starting');
        } else {
            showNotification(data.message || 'Failed to start server', 'error');
        }
    } catch (error) {
        console.error('Error starting server:', error);
        showNotification('Failed to start server', 'error');
    }
}

// Stop server
async function stopServer() {
    if (currentStatus === 'stopped') {
        showNotification('Server is already stopped', 'warning');
        return;
    }
    
    try {
        showNotification('Stopping server...', 'info');
        const response = await fetch('/api/server/stop', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Server stopped successfully', 'success');
            updateServerStatus('stopped');
        } else {
            showNotification(data.message || 'Failed to stop server', 'error');
        }
    } catch (error) {
        console.error('Error stopping server:', error);
        showNotification('Failed to stop server', 'error');
    }
}

// Display logs
function displayLogs(logs) {
    const logsContainer = document.getElementById('serverLogs');
    logsContainer.innerHTML = '';
    
    if (!logs || logs.length === 0) {
        logsContainer.innerHTML = '<div class="log-entry"><span class="log-time">--:--:--</span><span class="log-message">No logs available</span></div>';
        return;
    }
    
    logs.forEach(log => {
        addLogEntry(log.timestamp, log.message);
    });
    
    // Auto-scroll to bottom
    logsContainer.scrollTop = logsContainer.scrollHeight;
}

// Add single log entry
function addLogEntry(timestamp, message) {
    const logsContainer = document.getElementById('serverLogs');
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    
    // Determine log type based on message content
    let logClass = '';
    if (message.toLowerCase().includes('error') || message.toLowerCase().includes('exception')) {
        logClass = 'log-error';
    } else if (message.toLowerCase().includes('warn')) {
        logClass = 'log-warning';
    } else if (message.toLowerCase().includes('info')) {
        logClass = 'log-info';
    }
    
    logEntry.innerHTML = `
        <span class="log-time">${timestamp}</span>
        <span class="log-message ${logClass}">${escapeHtml(message)}</span>
    `;
    
    logsContainer.appendChild(logEntry);
    
    // Keep only last 100 log entries for performance
    while (logsContainer.children.length > 100) {
        logsContainer.removeChild(logsContainer.firstChild);
    }
    
    // Auto-scroll to bottom
    logsContainer.scrollTop = logsContainer.scrollHeight;
}

// Load installed mods
async function loadInstalledMods() {
    try {
        const response = await fetch('/api/mods/installed');
        const data = await response.json();
        
        installedMods = data;
        displayInstalledMods();
        document.getElementById('modCount').textContent = data.length;
    } catch (error) {
        console.error('Error loading installed mods:', error);
        showNotification('Failed to load installed mods', 'error');
    }
}

// Display installed mods
function displayInstalledMods() {
    const container = document.getElementById('installedMods');
    
    if (!installedMods || installedMods.length === 0) {
        container.innerHTML = '<div class="text-muted">No mods installed</div>';
        return;
    }
    
    container.innerHTML = installedMods.map(mod => `
        <div class="mod-item installed-mod-item">
            <div class="mod-info">
                <div class="mod-name">${mod.filename}</div>
                <div class="mod-meta">
                    Size: ${formatFileSize(mod.size)} | Modified: ${mod.modified}
                </div>
            </div>
            <div class="mod-actions">
                <button class="btn btn-danger btn-sm" onclick="removeMod('${mod.filename}')">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
}

// Search mods
async function searchMods() {
    const query = document.getElementById('modSearch').value.trim();
    
    if (!query) {
        showNotification('Please enter a search term', 'warning');
        return;
    }
    
    try {
        showNotification('Searching mods...', 'info');
        
        const response = await fetch(`/api/mods/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        if (data.error) {
            showNotification(data.error, 'error');
            return;
        }
        
        searchResults = data.hits || [];
        displaySearchResults();
        
        if (searchResults.length === 0) {
            showNotification('No mods found for your search', 'warning');
        } else {
            showNotification(`Found ${searchResults.length} mods`, 'success');
        }
    } catch (error) {
        console.error('Error searching mods:', error);
        showNotification('Failed to search mods', 'error');
    }
}

// Display search results
function displaySearchResults() {
    const container = document.getElementById('searchResults');
    const resultsContainer = document.getElementById('searchResultsContainer');
    
    if (!searchResults || searchResults.length === 0) {
        container.style.display = 'none';
        return;
    }
    
    container.style.display = 'block';
    
    resultsContainer.innerHTML = searchResults.map(mod => `
        <div class="mod-item search-mod-item">
            <div class="mod-icon">
                ${mod.icon_url ? `<img src="${mod.icon_url}" alt="${mod.title}" class="mod-image">` : '<div class="mod-image-placeholder"><i class="fas fa-puzzle-piece"></i></div>'}
            </div>
            <div class="mod-info">
                <div class="mod-header">
                    <div class="mod-name">${mod.title}</div>
                    <div class="mod-type">${mod.project_type || 'mod'}</div>
                </div>
                <div class="mod-description">${mod.description}</div>
                <div class="mod-categories">
                    ${mod.categories ? mod.categories.slice(0, 3).map(cat => `<span class="category-badge">${cat}</span>`).join('') : ''}
                </div>
                <div class="mod-compatibility">
                    <div class="compatibility-info">
                        <span class="compatibility-label">Client:</span>
                        <span class="compatibility-value ${getCompatibilityClass(mod.client_side)}">${mod.client_side || 'unknown'}</span>
                    </div>
                    <div class="compatibility-info">
                        <span class="compatibility-label">Server:</span>
                        <span class="compatibility-value ${getCompatibilityClass(mod.server_side)}">${mod.server_side || 'unknown'}</span>
                    </div>
                </div>
                <div class="mod-versions">
                    <span class="versions-label">Minecraft:</span>
                    <span class="versions-list">${mod.game_versions ? mod.game_versions.slice(-3).join(', ') : 'Unknown'}</span>
                </div>
                <div class="mod-meta">
                    <span class="downloads"><i class="fas fa-download"></i> ${formatNumber(mod.downloads)}</span>
                    <span class="updated">Updated: ${new Date(mod.date_modified).toLocaleDateString()}</span>
                </div>
            </div>
            <div class="mod-actions">
                <button class="btn btn-primary btn-sm" onclick="showModDetails('${mod.project_id}')">
                    <i class="fas fa-info-circle"></i> Details
                </button>
                <button class="btn btn-success btn-sm" onclick="installMod('${mod.project_id}')">
                    <i class="fas fa-download"></i> Install
                </button>
            </div>
        </div>
    `).join('');
}

// Install mod
async function installMod(modId) {
    try {
        showNotification('Installing mod...', 'info');
        
        const response = await fetch('/api/mods/install', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                mod_id: modId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message || 'Mod installed successfully', 'success');
            loadInstalledMods();
        } else {
            showNotification(data.message || 'Failed to install mod', 'error');
        }
    } catch (error) {
        console.error('Error installing mod:', error);
        showNotification('Failed to install mod', 'error');
    }
}

// Remove mod
async function removeMod(filename) {
    if (!confirm(`Are you sure you want to remove ${filename}?`)) {
        return;
    }
    
    try {
        showNotification('Removing mod...', 'info');
        
        const response = await fetch('/api/mods/remove', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                filename: filename
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification(data.message || 'Mod removed successfully', 'success');
            loadInstalledMods();
        } else {
            showNotification(data.message || 'Failed to remove mod', 'error');
        }
    } catch (error) {
        console.error('Error removing mod:', error);
        showNotification('Failed to remove mod', 'error');
    }
}

// Create share link
async function createShareLink() {
    try {
        const response = await fetch('/api/share/create', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const data = await response.json();
        
        if (data.share_id) {
            const shareUrl = `${window.location.origin}/share/${data.share_id}`;
            document.getElementById('shareLink').value = shareUrl;
            
            const modal = new bootstrap.Modal(document.getElementById('shareModal'));
            modal.show();
        } else {
            showNotification('Failed to create share link', 'error');
        }
    } catch (error) {
        console.error('Error creating share link:', error);
        showNotification('Failed to create share link', 'error');
    }
}

// Copy share link
function copyShareLink() {
    const shareLink = document.getElementById('shareLink');
    shareLink.select();
    shareLink.setSelectionRange(0, 99999);
    
    try {
        document.execCommand('copy');
        showNotification('Share link copied to clipboard!', 'success');
    } catch (error) {
        console.error('Error copying to clipboard:', error);
        showNotification('Failed to copy link', 'error');
    }
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(n => n.remove());
    
    // Create new notification
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
    
    // Also log to console
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// Helper functions for mod display
function getCompatibilityClass(compatibility) {
    switch(compatibility) {
        case 'required': return 'compat-required';
        case 'optional': return 'compat-optional';
        case 'unsupported': return 'compat-unsupported';
        default: return 'compat-unknown';
    }
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// Show detailed mod information
async function showModDetails(modId) {
    try {
        const response = await fetch(`https://api.modrinth.com/v2/project/${modId}`);
        const mod = await response.json();
        
        // Create modal content
        const modalContent = `
            <div class="modal fade" id="modDetailsModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">
                                ${mod.icon_url ? `<img src="${mod.icon_url}" alt="${mod.title}" class="modal-mod-icon">` : ''}
                                ${mod.title}
                            </h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mod-details-content">
                                <div class="mod-description-full">
                                    <p>${mod.description}</p>
                                </div>
                                
                                <div class="mod-stats">
                                    <div class="stat-item">
                                        <strong>Downloads:</strong> ${formatNumber(mod.downloads)}
                                    </div>
                                    <div class="stat-item">
                                        <strong>Followers:</strong> ${formatNumber(mod.followers)}
                                    </div>
                                    <div class="stat-item">
                                        <strong>Updated:</strong> ${new Date(mod.updated).toLocaleDateString()}
                                    </div>
                                    <div class="stat-item">
                                        <strong>License:</strong> ${mod.license ? mod.license.name : 'Unknown'}
                                    </div>
                                </div>
                                
                                <div class="mod-compatibility-full">
                                    <h6>Compatibility</h6>
                                    <div class="compatibility-grid">
                                        <div class="compatibility-item">
                                            <strong>Client Side:</strong>
                                            <span class="compatibility-value ${getCompatibilityClass(mod.client_side)}">${mod.client_side}</span>
                                        </div>
                                        <div class="compatibility-item">
                                            <strong>Server Side:</strong>
                                            <span class="compatibility-value ${getCompatibilityClass(mod.server_side)}">${mod.server_side}</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="mod-versions-full">
                                    <h6>Supported Versions</h6>
                                    <div class="versions-grid">
                                        <div class="versions-item">
                                            <strong>Minecraft:</strong>
                                            <div class="version-tags">
                                                ${mod.game_versions ? mod.game_versions.slice(-5).map(v => `<span class="version-tag">${v}</span>`).join('') : 'Unknown'}
                                            </div>
                                        </div>
                                        <div class="versions-item">
                                            <strong>Loaders:</strong>
                                            <div class="version-tags">
                                                ${mod.loaders ? mod.loaders.map(l => `<span class="loader-tag">${l}</span>`).join('') : 'Unknown'}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                ${mod.gallery && mod.gallery.length > 0 ? `
                                    <div class="mod-gallery">
                                        <h6>Screenshots</h6>
                                        <div class="gallery-grid">
                                            ${mod.gallery.slice(0, 4).map(img => `
                                                <img src="${img.url}" alt="${img.title || 'Screenshot'}" class="gallery-image" onclick="openImageModal('${img.url}', '${img.title || 'Screenshot'}')">
                                            `).join('')}
                                        </div>
                                    </div>
                                ` : ''}
                                
                                <div class="mod-links">
                                    ${mod.source_url ? `<a href="${mod.source_url}" target="_blank" class="btn btn-outline-primary btn-sm"><i class="fab fa-github"></i> Source</a>` : ''}
                                    ${mod.issues_url ? `<a href="${mod.issues_url}" target="_blank" class="btn btn-outline-secondary btn-sm"><i class="fas fa-bug"></i> Issues</a>` : ''}
                                    ${mod.wiki_url ? `<a href="${mod.wiki_url}" target="_blank" class="btn btn-outline-info btn-sm"><i class="fas fa-book"></i> Wiki</a>` : ''}
                                    ${mod.discord_url ? `<a href="${mod.discord_url}" target="_blank" class="btn btn-outline-primary btn-sm"><i class="fab fa-discord"></i> Discord</a>` : ''}
                                </div>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <button type="button" class="btn btn-success" onclick="installMod('${mod.id}'); bootstrap.Modal.getInstance(document.getElementById('modDetailsModal')).hide();">
                                <i class="fas fa-download"></i> Install Mod
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('modDetailsModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalContent);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('modDetailsModal'));
        modal.show();
        
    } catch (error) {
        console.error('Error fetching mod details:', error);
        showNotification('Failed to load mod details', 'error');
    }
}

// Open image in modal
function openImageModal(imageUrl, title) {
    const imageModalContent = `
        <div class="modal fade" id="imageModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body text-center">
                        <img src="${imageUrl}" alt="${title}" class="img-fluid">
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing image modal if any
    const existingImageModal = document.getElementById('imageModal');
    if (existingImageModal) {
        existingImageModal.remove();
    }
    
    // Add modal to body
    document.body.insertAdjacentHTML('beforeend', imageModalContent);
    
    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('imageModal'));
    modal.show();
}

// Server command functions
function sendServerCommand() {
    const commandInput = document.getElementById('serverCommand');
    const command = commandInput.value.trim();
    
    if (!command) {
        showNotification('Please enter a command', 'warning');
        return;
    }
    
    // Send command via WebSocket
    socket.emit('send_command', { command: command });
    commandInput.value = '';
    
    // Show command being sent
    addLogEntry(new Date().toLocaleTimeString(), `> ${command}`, 'command-sent');
}

function quickCommand(command) {
    document.getElementById('serverCommand').value = command;
    sendServerCommand();
}

function handleCommandResult(data) {
    const type = data.success ? 'success' : 'error';
    showNotification(data.message, type);
    
    if (data.success) {
        addLogEntry(new Date().toLocaleTimeString(), `Command executed: ${data.command}`, 'command-success');
    }
}

// Server configuration functions
async function openServerConfig() {
    const modal = new bootstrap.Modal(document.getElementById('serverConfigModal'));
    modal.show();
    
    try {
        const response = await fetch('/api/server/config');
        const data = await response.json();
        
        displayServerConfig(data.config, data.default_config);
        document.getElementById('saveConfigBtn').disabled = false;
    } catch (error) {
        console.error('Error loading server config:', error);
        document.getElementById('configContent').innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i>
                Failed to load server configuration: ${error.message}
            </div>
        `;
    }
}

function displayServerConfig(config, defaultConfig) {
    const configSections = {
        'Server Settings': ['server-port', 'motd', 'max-players', 'online-mode'],
        'World Settings': ['level-name', 'level-type', 'difficulty', 'gamemode', 'spawn-protection'],
        'Network Settings': ['enable-rcon', 'rcon.port', 'rcon.password', 'view-distance'],
        'Game Rules': ['pvp', 'spawn-monsters', 'spawn-animals', 'spawn-npcs', 'enable-command-block']
    };
    
    let html = '<form id="serverConfigForm">';
    
    for (const [sectionName, keys] of Object.entries(configSections)) {
        html += `
            <div class="config-section">
                <h6 class="config-section-title">${sectionName}</h6>
                <div class="row">
        `;
        
        keys.forEach(key => {
            const value = config[key] || defaultConfig[key] || '';
            const label = key.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            
            html += `
                <div class="col-md-6 mb-3">
                    <label for="config_${key}" class="form-label">${label}</label>
                    ${getConfigInput(key, value)}
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    }
    
    html += '</form>';
    document.getElementById('configContent').innerHTML = html;
}

function getConfigInput(key, value) {
    const booleanFields = ['online-mode', 'enable-rcon', 'pvp', 'spawn-monsters', 'spawn-animals', 'spawn-npcs', 'enable-command-block'];
    const selectFields = {
        'difficulty': ['peaceful', 'easy', 'normal', 'hard'],
        'gamemode': ['survival', 'creative', 'adventure', 'spectator'],
        'level-type': ['default', 'flat', 'largeBiomes', 'amplified']
    };
    
    if (booleanFields.includes(key)) {
        return `
            <select class="form-select" id="config_${key}" name="${key}">
                <option value="true" ${value === 'true' ? 'selected' : ''}>True</option>
                <option value="false" ${value === 'false' ? 'selected' : ''}>False</option>
            </select>
        `;
    } else if (selectFields[key]) {
        let options = selectFields[key].map(option => 
            `<option value="${option}" ${value === option ? 'selected' : ''}>${option.charAt(0).toUpperCase() + option.slice(1)}</option>`
        ).join('');
        return `<select class="form-select" id="config_${key}" name="${key}">${options}</select>`;
    } else {
        const inputType = ['server-port', 'rcon.port', 'max-players', 'spawn-protection', 'view-distance'].includes(key) ? 'number' : 'text';
        return `<input type="${inputType}" class="form-control" id="config_${key}" name="${key}" value="${value}">`;
    }
}

async function saveServerConfig() {
    const form = document.getElementById('serverConfigForm');
    const formData = new FormData(form);
    const config = {};
    
    for (let [key, value] of formData.entries()) {
        config[key] = value;
    }
    
    try {
        showNotification('Saving configuration...', 'info');
        
        const response = await fetch('/api/server/config', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ config: config })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('Configuration saved successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('serverConfigModal')).hide();
        } else {
            showNotification(data.message || 'Failed to save configuration', 'error');
        }
    } catch (error) {
        console.error('Error saving config:', error);
        showNotification('Failed to save configuration', 'error');
    }
}

function showServerFiles() {
    const modal = new bootstrap.Modal(document.getElementById('serverFilesModal'));
    modal.show();
}

// Auto-refresh status periodically
setInterval(loadServerStatus, 30000); // Every 30 seconds 

// Load user profile information
async function loadUserProfile() {
    try {
        const response = await fetch('/api/user/profile');
        const user = await response.json();
        
        document.getElementById('userDisplayName').textContent = user.display_name || user.username;
        
        // Update profile modal if it exists
        const profileUsername = document.getElementById('profileUsername');
        if (profileUsername) {
            profileUsername.value = user.username;
            document.getElementById('profileDisplayName').value = user.display_name;
            document.getElementById('profileEmail').value = user.email;
            document.getElementById('profileRole').value = user.role.charAt(0).toUpperCase() + user.role.slice(1);
        }
    } catch (error) {
        console.error('Error loading user profile:', error);
    }
}

// Load available nodes
async function loadNodes() {
    try {
        const response = await fetch('/api/nodes');
        if (response.ok) {
            const nodes = await response.json();
            updateNodesDisplay(nodes);
        }
    } catch (error) {
        console.error('Error loading nodes:', error);
    }
}

// Update nodes display
function updateNodesDisplay(nodes) {
    const nodeCount = document.getElementById('nodeCount');
    const nodesList = document.getElementById('nodesList');
    
    if (nodeCount) {
        nodeCount.textContent = nodes.length;
    }
    
    if (nodesList) {
        if (nodes.length === 0) {
            nodesList.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-desktop fa-3x mb-3"></i>
                    <p>No computers detected</p>
                    <small>Your computer will appear here as "Master Node" once scanning starts.<br/>
                    Install The Originals on other computers to manage them remotely.</small>
                </div>
            `;
        } else {
            nodesList.innerHTML = nodes.map(node => `
                <div class="node-item ${node.status}">
                    <div class="node-info">
                        <div class="node-header">
                            <strong>${node.name}</strong>
                            <span class="badge bg-${getNodeStatusColor(node.status)}">${node.status.toUpperCase()}</span>
                        </div>
                        <div class="node-details">
                            <span><i class="fas fa-network-wired"></i> ${node.ip_address}:${node.port}</span>
                            <span><i class="fas fa-microchip"></i> ${node.capabilities.cpu_cores || 'N/A'} cores</span>
                            <span><i class="fas fa-memory"></i> ${node.capabilities.ram_gb || 'N/A'} GB RAM</span>
                            <span><i class="fas fa-hdd"></i> ${node.capabilities.disk_gb || 'N/A'} GB disk</span>
                        </div>
                    </div>
                    <div class="node-actions">
                        ${node.is_master ? `
                            <button class="btn btn-sm btn-success" disabled>
                                <i class="fas fa-crown"></i> Master
                            </button>
                        ` : node.status === 'online' ? `
                            <button class="btn btn-sm btn-primary me-1" onclick="deployToNode(${node.id})">
                                <i class="fas fa-rocket"></i> Deploy
                            </button>
                            <button class="btn btn-sm btn-outline-secondary me-1" onclick="connectToNode(${node.id})">
                                <i class="fas fa-link"></i> Connect
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="removeNode(${node.id})" title="Remove Node">
                                <i class="fas fa-trash"></i>
                            </button>
                        ` : `
                            <button class="btn btn-sm btn-outline-secondary me-1" disabled>
                                <i class="fas fa-times"></i> Offline
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="removeNode(${node.id})" title="Remove Node">
                                <i class="fas fa-trash"></i>
                            </button>
                        `}
                    </div>
                </div>
            `).join('');
        }
    }
}

function getNodeStatusColor(status) {
    switch(status) {
        case 'online': return 'success';
        case 'connecting': return 'warning';
        case 'offline': return 'secondary';
        default: return 'danger';
    }
}

// User profile functions
async function openUserProfile() {
    await loadUserProfile();
    const modal = new bootstrap.Modal(document.getElementById('userProfileModal'));
    modal.show();
}

async function saveUserProfile() {
    const profileData = {
        display_name: document.getElementById('profileDisplayName').value,
        email: document.getElementById('profileEmail').value
    };
    
    try {
        const response = await fetch('/api/user/profile', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(profileData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Profile updated successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('userProfileModal')).hide();
            loadUserProfile(); // Refresh display
        } else {
            showNotification(result.message || 'Failed to update profile', 'error');
        }
    } catch (error) {
        console.error('Error saving profile:', error);
        showNotification('Failed to update profile', 'error');
    }
}

// Multi-computer management functions
function openNodesManager() {
    const modal = new bootstrap.Modal(document.getElementById('nodesManagerModal'));
    modal.show();
    loadNodes();
    detectLocalIP();
}

async function detectLocalIP() {
    try {
        // Simple way to get local IP - create a connection and check local address
        const localIPElement = document.getElementById('localIP');
        if (localIPElement) {
            localIPElement.textContent = window.location.hostname;
        }
    } catch (error) {
        console.error('Error detecting IP:', error);
    }
}

async function scanForNodes() {
    showNotification('🔍 Scanning network for computers...', 'info');
    
    // Update the scan button to show progress
    const scanButton = document.querySelector('button[onclick="scanForNodes()"]');
    if (scanButton) {
        scanButton.disabled = true;
        scanButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scanning...';
    }
    
    // Trigger a refresh of nodes
    setTimeout(() => {
        loadNodes();
        showNotification('✅ Network scan completed! Your computer should now appear as Master Node.', 'success');
        
        // Reset the scan button
        if (scanButton) {
            scanButton.disabled = false;
            scanButton.innerHTML = '<i class="fas fa-search"></i> Scan Network';
        }
    }, 3000);
}

async function deployToNode(nodeId) {
    const result = confirm('Deploy server to this computer? This will copy the current server configuration.');
    if (!result) return;
    
    try {
        showNotification('Deploying server...', 'info');
        
        const serverConfig = {
            name: 'The Originals Server',
            minecraft_version: '1.20.1',
            server_type: 'fabric',
            port: 25565,
            max_players: 20
        };
        
        const response = await fetch(`/api/nodes/${nodeId}/deploy`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(serverConfig)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Server deployed successfully!', 'success');
        } else {
            showNotification(result.message || 'Failed to deploy server', 'error');
        }
    } catch (error) {
        console.error('Error deploying server:', error);
        showNotification('Failed to deploy server', 'error');
    }
}

function connectToNode(nodeId) {
    showNotification('This feature will allow you to switch server control to another computer', 'info');
    // TODO: Implement node switching
}

function deployServerDialog() {
    showNotification('Select a computer from the list to deploy a server to it', 'info');
}

function showNodeGuide() {
    const guideContent = `
        <div class="alert alert-info">
            <h6><i class="fas fa-info-circle"></i> Multi-Computer Setup Guide</h6>
            <ol>
                <li><strong>Install The Originals</strong> on each computer you want to use</li>
                <li><strong>Run the application</strong> on each computer (they'll auto-discover each other)</li>
                <li><strong>Deploy servers</strong> to different computers as needed</li>
                <li><strong>Switch control</strong> between computers without stopping servers</li>
            </ol>
            <p><strong>Benefits:</strong></p>
            <ul>
                <li>Distribute server load across multiple computers</li>
                <li>Keep servers running even if one computer shuts down</li>
                <li>Centralized management of all your computers</li>
            </ul>
        </div>
    `;
    
    const tempModal = document.createElement('div');
    tempModal.innerHTML = `
        <div class="modal fade" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Multi-Computer Setup Guide</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        ${guideContent}
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(tempModal);
    const modal = new bootstrap.Modal(tempModal.firstElementChild);
    modal.show();
    
    tempModal.firstElementChild.addEventListener('hidden.bs.modal', function() {
        document.body.removeChild(tempModal);
    });
} 

function showAddNodeDialog() {
    const modal = new bootstrap.Modal(document.getElementById('addNodeModal'));
    modal.show();
    
    // Clear form
    document.getElementById('addNodeForm').reset();
    document.getElementById('nodePort').value = '3000';
}

async function addNodeManually() {
    const name = document.getElementById('nodeName').value.trim();
    const ip = document.getElementById('nodeIP').value.trim();
    const port = document.getElementById('nodePort').value;
    
    if (!name || !ip) {
        showNotification('Please fill in all required fields', 'error');
        return;
    }
    
    // Validate IP address format
    const ipRegex = /^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$/;
    if (!ipRegex.test(ip)) {
        showNotification('Please enter a valid IP address', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/nodes/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name: name,
                ip_address: ip,
                port: parseInt(port)
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Computer added successfully!', 'success');
            
            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addNodeModal'));
            modal.hide();
            
            // Refresh nodes list
            loadNodes();
        } else {
            showNotification(result.error || 'Failed to add computer', 'error');
        }
    } catch (error) {
        console.error('Error adding node:', error);
        showNotification('Failed to add computer', 'error');
        }
}

async function removeNode(nodeId) {
    if (!confirm('Are you sure you want to remove this computer? This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/nodes/${nodeId}/remove`, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Computer removed successfully!', 'success');
            loadNodes(); // Refresh the nodes list
        } else {
            showNotification(result.error || 'Failed to remove computer', 'error');
        }
    } catch (error) {
        console.error('Error removing node:', error);
        showNotification('Failed to remove computer', 'error');
    }
}

// Public Tunnel Management
async function loadTunnelStatus() {
    try {
        const response = await fetch('/api/tunnel/status');
        const data = await response.json();
        updateTunnelStatus(data);
    } catch (error) {
        console.error('Error loading tunnel status:', error);
    }
}

function updateTunnelStatus(status) {
    const tunnelStatusBar = document.getElementById('tunnelStatusBar');
    const tunnelBtn = document.getElementById('tunnelBtn');
    const tunnelBtnText = document.getElementById('tunnelBtnText');
    const tunnelUrl = document.getElementById('tunnelUrl');
    
    if (status.status === 'running') {
        // Show status bar
        tunnelStatusBar.style.display = 'block';
        
        // Update URL
        if (tunnelUrl && status.url) {
            tunnelUrl.value = status.url;
        }
        
        // Update button
        if (tunnelBtn) {
            tunnelBtn.className = 'btn btn-outline-danger ms-2';
            tunnelBtn.innerHTML = '<i class="fas fa-stop"></i> <span id="tunnelBtnText">Stop Public</span>';
        }
    } else {
        // Hide status bar
        tunnelStatusBar.style.display = 'none';
        
        // Update button
        if (tunnelBtn) {
            tunnelBtn.className = 'btn btn-outline-success ms-2';
            tunnelBtn.innerHTML = '<i class="fas fa-globe"></i> <span id="tunnelBtnText">Go Public</span>';
        }
    }
}

async function toggleTunnel() {
    const tunnelBtn = document.getElementById('tunnelBtn');
    const tunnelBtnText = document.getElementById('tunnelBtnText');
    
    // Disable button during operation
    if (tunnelBtn) {
        tunnelBtn.disabled = true;
        tunnelBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> <span>Working...</span>';
    }
    
    try {
        // Check current status first
        const statusResponse = await fetch('/api/tunnel/status');
        const currentStatus = await statusResponse.json();
        
        let response;
        if (currentStatus.status === 'running') {
            // Stop tunnel
            response = await fetch('/api/tunnel/stop', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
        } else {
            // Start tunnel
            showNotification('🚀 Starting public tunnel... This may take a moment!', 'info');
            response = await fetch('/api/tunnel/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
        }
        
        const data = await response.json();
        
        if (data.success) {
            if (currentStatus.status === 'running') {
                showNotification('🔒 Public access stopped successfully!', 'success');
            } else {
                showNotification(`🌐 Server is now PUBLIC! URL: ${data.url || 'Loading...'}`, 'success');
            }
            
            // Refresh status
            setTimeout(loadTunnelStatus, 1000);
        } else {
            showNotification(`❌ Error: ${data.message}`, 'error');
        }
        
    } catch (error) {
        console.error('Error toggling tunnel:', error);
        showNotification('❌ Failed to toggle public access', 'error');
    } finally {
        // Re-enable button
        if (tunnelBtn) {
            tunnelBtn.disabled = false;
        }
        // Status will be updated by loadTunnelStatus
        setTimeout(loadTunnelStatus, 500);
    }
}

function copyTunnelUrl() {
    const tunnelUrl = document.getElementById('tunnelUrl');
    if (tunnelUrl && tunnelUrl.value) {
        tunnelUrl.select();
        tunnelUrl.setSelectionRange(0, 99999);
        
        try {
            document.execCommand('copy');
            showNotification('🔗 Public URL copied to clipboard!', 'success');
        } catch (error) {
            console.error('Error copying to clipboard:', error);
            showNotification('Failed to copy URL', 'error');
        }
    }
}

// Professional Application Features

// Update status indicators in navbar
function updateStatusIndicators() {
    // Update server status badge
    const serverStatusBadge = document.getElementById('serverStatusBadge');
    if (serverStatusBadge) {
        fetch('/api/server/status')
            .then(response => response.json())
            .then(data => {
                const isRunning = data.status === 'running';
                serverStatusBadge.className = `badge ${isRunning ? 'bg-success' : 'bg-secondary'} me-2`;
                serverStatusBadge.innerHTML = `<i class="fas fa-circle"></i> Server ${isRunning ? 'Online' : 'Offline'}`;
            })
            .catch(() => {
                serverStatusBadge.className = 'badge bg-danger me-2';
                serverStatusBadge.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
            });
    }
    
    // Update tunnel status badge
    const tunnelStatusBadge = document.getElementById('tunnelStatusBadge');
    if (tunnelStatusBadge) {
        fetch('/api/tunnel/status')
            .then(response => response.json())
            .then(data => {
                const isRunning = data.status === 'running';
                tunnelStatusBadge.className = `badge ${isRunning ? 'bg-success' : 'bg-secondary'} me-2`;
                tunnelStatusBadge.innerHTML = `<i class="fas fa-globe"></i> Tunnel ${isRunning ? 'Active' : 'Off'}`;
            })
            .catch(() => {
                tunnelStatusBadge.className = 'badge bg-secondary me-2';
                tunnelStatusBadge.innerHTML = '<i class="fas fa-globe"></i> Tunnel Off';
            });
    }
    
    // Update node count badge
    const nodeCountText = document.getElementById('nodeCountText');
    if (nodeCountText) {
        fetch('/api/nodes')
            .then(response => response.json())
            .then(data => {
                nodeCountText.textContent = data.length;
            })
            .catch(() => {
                nodeCountText.textContent = '0';
            });
    }
}

// User Management (Admin only)
async function openUserManagement() {
    try {
        const response = await fetch('/api/admin/users');
        if (!response.ok) {
            throw new Error('Permission denied');
        }
        
        const users = await response.json();
        showNotification(`Loaded ${users.length} users for management`, 'success');
        
        // TODO: Create user management modal interface
        // This is a placeholder - full implementation would create a detailed modal
        
    } catch (error) {
        showNotification('Failed to load user management: ' + error.message, 'error');
    }
}

// About & Updates Dialog
function showAbout() {
    const aboutHtml = `
        <div class="modal fade" id="aboutModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header bg-gradient text-white" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                        <h5 class="modal-title">
                            <i class="fas fa-cube me-2"></i>About The Originals
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="text-center mb-4">
                            <i class="fas fa-cube text-primary" style="font-size: 4rem;"></i>
                            <h3 class="mt-3">The Originals</h3>
                            <p class="text-muted">Minecraft Server Manager v2.0.0</p>
                        </div>
                        
                        <div class="row">
                            <div class="col-md-6">
                                <h6><i class="fas fa-star text-warning me-2"></i>Features</h6>
                                <ul class="list-unstyled">
                                    <li><i class="fas fa-check text-success me-2"></i>Easy server management</li>
                                    <li><i class="fas fa-check text-success me-2"></i>Multi-computer support</li>
                                    <li><i class="fas fa-check text-success me-2"></i>Public tunnels</li>
                                    <li><i class="fas fa-check text-success me-2"></i>Mod management</li>
                                    <li><i class="fas fa-check text-success me-2"></i>Real-time monitoring</li>
                                    <li><i class="fas fa-check text-success me-2"></i>User management</li>
                                </ul>
                            </div>
                            <div class="col-md-6">
                                <h6><i class="fas fa-info-circle text-primary me-2"></i>System Info</h6>
                                <ul class="list-unstyled">
                                    <li><strong>Version:</strong> 2.0.0</li>
                                    <li><strong>Build:</strong> Professional</li>
                                    <li><strong>Platform:</strong> Cross-platform</li>
                                    <li><strong>License:</strong> Proprietary</li>
                                    <li><strong>Support:</strong> Community</li>
                                </ul>
                            </div>
                        </div>
                        
                        <div class="alert alert-info mt-4">
                            <h6><i class="fas fa-rocket me-2"></i>What's New in v2.0.0</h6>
                            <ul class="mb-0">
                                <li>Enhanced professional UI design</li>
                                <li>Improved user management system</li>
                                <li>Better node registration and discovery</li>
                                <li>Real-time status indicators</li>
                                <li>Professional application structure</li>
                            </ul>
                        </div>
                        
                        <div class="text-center mt-4">
                            <button class="btn btn-primary me-2" onclick="checkForUpdates()">
                                <i class="fas fa-download me-2"></i>Check for Updates
                            </button>
                            <button class="btn btn-outline-secondary" onclick="openSystemLogs()">
                                <i class="fas fa-file-alt me-2"></i>System Logs
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', aboutHtml);
    const modal = new bootstrap.Modal(document.getElementById('aboutModal'));
    modal.show();
    
    document.getElementById('aboutModal').addEventListener('hidden.bs.modal', function() {
        this.remove();
    });
}

// Enhanced Auto-update client functionality
let updateNotificationShown = false;
let updateCheckInterval = null;

// Enhanced Socket event handlers for updates
socket.on('update_available', function(data) {
    showUpdateNotification(data);
});

socket.on('update_progress', function(data) {
    updateProgressBar(data);
});

socket.on('update_error', function(data) {
    showNotification('Update failed: ' + data.message, 'error');
});

socket.on('update_check_result', function(data) {
    if (data.update_available) {
        showUpdateNotification(data);
    } else {
        showNotification('You are running the latest version!', 'success');
    }
});

socket.on('update_triggered', function(data) {
    showNotification('Update check triggered!', 'info');
    if (data.result.update_available) {
        showUpdateNotification(data.result);
    }
});

// Enhanced update notification with modern UI
function showUpdateNotification(updateInfo) {
    if (updateNotificationShown) return;
    updateNotificationShown = true;
    
    const isSecurityUpdate = updateInfo.security_update;
    const alertClass = isSecurityUpdate ? 'alert-warning' : 'alert-info';
    const icon = isSecurityUpdate ? 'fas fa-shield-alt' : 'fas fa-download';
    const priority = isSecurityUpdate ? 'SECURITY UPDATE' : 'UPDATE AVAILABLE';
    
    const fileSize = updateInfo.file_size ? formatFileSize(updateInfo.file_size) : 'Unknown size';
    
    const notification = `
        <div class="alert ${alertClass} alert-dismissible fade show update-notification position-fixed" 
             style="top: 20px; right: 20px; z-index: 9999; max-width: 400px; box-shadow: 0 4px 12px rgba(0,0,0,0.3);" 
             role="alert">
            <div class="d-flex align-items-center mb-2">
                <i class="${icon} me-2"></i>
                <strong>${priority}</strong>
            </div>
            <h6 class="mb-1">Version ${updateInfo.version} Available!</h6>
            <small class="text-muted">Current: ${updateInfo.current_version} | Size: ${fileSize}</small>
            
            ${updateInfo.release_notes ? `
                <div class="mt-2 p-2 bg-light rounded">
                    <small>${updateInfo.release_notes.substring(0, 200)}${updateInfo.release_notes.length > 200 ? '...' : ''}</small>
                </div>
            ` : ''}
            
            <div class="d-flex gap-2 mt-3">
                <button class="btn btn-primary btn-sm" onclick="downloadUpdate()" ${isSecurityUpdate ? 'style="background-color: #dc3545; border-color: #dc3545;"' : ''}>
                    <i class="fas fa-download me-1"></i>
                    ${isSecurityUpdate ? 'Install Security Update' : 'Update Now'}
                </button>
                <button class="btn btn-outline-secondary btn-sm" onclick="showReleaseNotes()">
                    <i class="fas fa-file-alt me-1"></i>Details
                </button>
                <button class="btn btn-outline-danger btn-sm" onclick="dismissUpdate()">
                    <i class="fas fa-times me-1"></i>Later
                </button>
            </div>
            
            <div class="progress mt-2 d-none" id="updateProgress">
                <div class="progress-bar progress-bar-striped progress-bar-animated" 
                     role="progressbar" style="width: 0%"></div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('afterbegin', notification);
    
    // Auto-close after 30 seconds for non-security updates
    if (!isSecurityUpdate) {
        setTimeout(() => {
            dismissUpdate();
        }, 30000);
    }
}

// Enhanced download function with progress
async function downloadUpdate() {
    const notification = document.querySelector('.update-notification');
    const progressBar = notification.querySelector('#updateProgress');
    
    if (!confirm('This will restart The Originals to apply the update. Any unsaved changes will be lost. Continue?')) {
        return;
    }
    
    try {
        // Show progress bar
        progressBar.classList.remove('d-none');
        
        const response = await fetch('/api/updates/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('Update is downloading and will install automatically...', 'info');
            
            // Update button states
            const buttons = notification.querySelectorAll('button');
            buttons.forEach(btn => btn.disabled = true);
            
        } else {
            showNotification('Update failed: ' + result.message, 'error');
            progressBar.classList.add('d-none');
        }
    } catch (error) {
        showNotification('Update failed: ' + error.message, 'error');
        progressBar.classList.add('d-none');
    }
}

// Enhanced progress bar updates
function updateProgressBar(data) {
    const progressBar = document.querySelector('#updateProgress .progress-bar');
    const notification = document.querySelector('.update-notification');
    
    if (!progressBar || !notification) return;
    
    const progress = Math.round(data.progress || 0);
    progressBar.style.width = progress + '%';
    progressBar.textContent = progress + '%';
    
    if (data.status === 'downloading') {
        const downloaded = data.downloaded ? formatFileSize(data.downloaded) : '';
        const total = data.total ? formatFileSize(data.total) : '';
        const sizeText = downloaded && total ? ` (${downloaded}/${total})` : '';
        
        notification.querySelector('h6').textContent = `Downloading... ${progress}%${sizeText}`;
        progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-info';
        
    } else if (data.status === 'installing') {
        notification.querySelector('h6').textContent = 'Installing update...';
        progressBar.className = 'progress-bar progress-bar-striped progress-bar-animated bg-success';
        progressBar.style.width = '100%';
        progressBar.textContent = 'Installing...';
        
        // Show countdown
        let countdown = 10;
        const countdownInterval = setInterval(() => {
            if (countdown <= 0) {
                clearInterval(countdownInterval);
                notification.querySelector('h6').textContent = 'Restarting application...';
            } else {
                notification.querySelector('h6').textContent = `Installing... Restarting in ${countdown}s`;
                countdown--;
            }
        }, 1000);
    }
}

// Manual check function
async function checkForUpdates() {
    try {
        showNotification('Checking for updates...', 'info');
        
        const response = await fetch('/api/updates/check?force=true');
        const result = await response.json();
        
        if (result.update_available) {
            showUpdateNotification(result);
        } else {
            showNotification('You are running the latest version!', 'success');
        }
    } catch (error) {
        showNotification('Failed to check for updates: ' + error.message, 'error');
    }
}

// Manual trigger via text input
function handleManualTrigger(text) {
    if (!text) return;
    
    fetch('/api/updates/trigger', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({text: text})
    })
    .then(response => response.json())
    .then(result => {
        if (result.triggered) {
            showNotification('Update check triggered!', 'info');
            if (result.result.update_available) {
                showUpdateNotification(result.result);
            }
        }
    })
    .catch(error => {
        console.error('Manual trigger error:', error);
    });
}

// Dismiss update notification
function dismissUpdate() {
    const notification = document.querySelector('.update-notification');
    if (notification) {
        notification.remove();
        updateNotificationShown = false;
    }
}

// Show release notes
function showReleaseNotes() {
    const notification = document.querySelector('.update-notification');
    if (!notification) return;
    
    const releaseNotes = notification.querySelector('.bg-light').innerHTML;
    const modal = `
        <div class="modal fade" id="releaseNotesModal" tabindex="-1">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Release Notes</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        ${releaseNotes}
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    document.body.insertAdjacentHTML('beforeend', modal);
    new bootstrap.Modal(document.getElementById('releaseNotesModal')).show();
}

function openSystemLogs() {
    showNotification('📄 System logs feature ready for implementation!', 'info');
}

// Initialize enhanced update system
document.addEventListener('DOMContentLoaded', function() {
    // Check for updates on page load (delayed to avoid conflicts)
    setTimeout(checkForUpdates, 10000);
    
    // Set up periodic checks (every 30 minutes in foreground)
    updateCheckInterval = setInterval(checkForUpdates, 30 * 60 * 1000);
    
    // Listen for manual triggers in command input
    const commandInput = document.querySelector('#commandInput');
    if (commandInput) {
        commandInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                handleManualTrigger(this.value);
            }
        });
    }
    
    // Listen for manual triggers in server command input
    const serverCommandInput = document.querySelector('#serverCommandInput');
    if (serverCommandInput) {
        serverCommandInput.addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                handleManualTrigger(this.value);
            }
        });
    }
    
    // Clean up on page unload
    window.addEventListener('beforeunload', function() {
        if (updateCheckInterval) {
            clearInterval(updateCheckInterval);
        }
    });
});

// Auto-refresh tunnel status every 30 seconds 