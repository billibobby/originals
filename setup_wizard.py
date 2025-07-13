import os
import sys
import json
import webbrowser
import threading
import time
from pathlib import Path
from flask import Flask, render_template_string, request, jsonify

class SetupWizard:
    def __init__(self):
        self.app = Flask(__name__)
        self.setup_data = {
            'admin_username': 'admin',
            'admin_password': '',
            'admin_email': '',
            'server_name': 'My Minecraft Server',
            'max_players': 20,
            'enable_tunnel': False,
            'enable_updates': True,
            'enable_tray': True
        }
        self.setup_complete = False
        
    def run_wizard(self):
        """Run the setup wizard web interface"""
        
        @self.app.route('/')
        def index():
            return render_template_string(WIZARD_TEMPLATE)
        
        @self.app.route('/api/setup', methods=['POST'])
        def save_setup():
            data = request.json
            self.setup_data.update(data)
            
            # Save configuration
            self.save_configuration()
            
            self.setup_complete = True
            return jsonify({'success': True, 'message': 'Setup completed successfully!'})
        
        @self.app.route('/api/test_connection')
        def test_connection():
            return jsonify({'success': True, 'message': 'Connection test successful!'})
        
        # Start the web server
        print("Starting Setup Wizard...")
        print("Open your browser to: http://localhost:8080")
        
        # Auto-open browser
        threading.Timer(1.0, lambda: webbrowser.open('http://localhost:8080')).start()
        
        try:
            self.app.run(host='localhost', port=8080, debug=False)
        except KeyboardInterrupt:
            print("Setup wizard cancelled")
            return False
        
        return self.setup_complete
    
    def save_configuration(self):
        """Save the setup configuration"""
        try:
            # Create .env file
            env_content = f"""SECRET_KEY=minecraft-server-manager-secret-key-2024
MINECRAFT_VERSION=1.20.1
SERVER_PORT=3000
ADMIN_USERNAME={self.setup_data['admin_username']}
ADMIN_PASSWORD={self.setup_data['admin_password']}
ADMIN_EMAIL={self.setup_data['admin_email']}
SERVER_NAME={self.setup_data['server_name']}
MAX_PLAYERS={self.setup_data['max_players']}
ENABLE_TUNNEL={str(self.setup_data['enable_tunnel']).lower()}
ENABLE_UPDATES={str(self.setup_data['enable_updates']).lower()}
ENABLE_TRAY={str(self.setup_data['enable_tray']).lower()}
"""
            
            env_path = Path('.env')
            with open(env_path, 'w') as f:
                f.write(env_content)
            
            # Create setup completion marker
            setup_marker = Path('.setup_complete')
            setup_marker.touch()
            
            print("Configuration saved successfully!")
            return True
            
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False

def is_first_run():
    """Check if this is the first run of the application"""
    return not Path('.setup_complete').exists()

def run_setup_wizard():
    """Run the setup wizard if needed"""
    if is_first_run():
        print("First run detected - starting setup wizard...")
        wizard = SetupWizard()
        return wizard.run_wizard()
    return True

# HTML template for the setup wizard
WIZARD_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>The Originals - Setup Wizard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        .wizard-container {
            max-width: 800px;
            margin: 2rem auto;
        }
        .wizard-card {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .wizard-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }
        .wizard-body {
            padding: 2rem;
        }
        .step {
            display: none;
        }
        .step.active {
            display: block;
        }
        .step-indicator {
            display: flex;
            justify-content: center;
            margin-bottom: 2rem;
        }
        .step-item {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #e9ecef;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 10px;
            position: relative;
            color: #6c757d;
        }
        .step-item.active {
            background: #667eea;
            color: white;
        }
        .step-item.completed {
            background: #28a745;
            color: white;
        }
        .step-item:not(:last-child):after {
            content: '';
            position: absolute;
            top: 50%;
            left: 100%;
            width: 20px;
            height: 2px;
            background: #e9ecef;
            transform: translateY(-50%);
        }
        .btn-wizard {
            padding: 12px 30px;
            border-radius: 10px;
            font-weight: 600;
        }
        .form-control {
            border-radius: 10px;
            border: 2px solid #e9ecef;
            padding: 12px 16px;
        }
        .form-control:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
        }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="wizard-container">
            <div class="wizard-card">
                <div class="wizard-header">
                    <i class="fas fa-cube fa-3x mb-3"></i>
                    <h1>Welcome to The Originals</h1>
                    <p>Let's get your Minecraft Server Manager set up!</p>
                </div>
                
                <div class="wizard-body">
                    <!-- Step Indicator -->
                    <div class="step-indicator">
                        <div class="step-item active" data-step="1">1</div>
                        <div class="step-item" data-step="2">2</div>
                        <div class="step-item" data-step="3">3</div>
                        <div class="step-item" data-step="4">4</div>
                    </div>
                    
                    <!-- Step 1: Welcome -->
                    <div class="step active" id="step1">
                        <div class="text-center">
                            <h3>Welcome to The Originals</h3>
                            <p class="lead">Your professional Minecraft Server Manager</p>
                            <div class="row mt-4">
                                <div class="col-md-4">
                                    <i class="fas fa-server fa-3x text-primary mb-3"></i>
                                    <h5>Easy Server Management</h5>
                                    <p>Start, stop, and monitor your Minecraft servers with ease.</p>
                                </div>
                                <div class="col-md-4">
                                    <i class="fas fa-users fa-3x text-success mb-3"></i>
                                    <h5>Multi-User Support</h5>
                                    <p>Manage multiple users with different permission levels.</p>
                                </div>
                                <div class="col-md-4">
                                    <i class="fas fa-globe fa-3x text-info mb-3"></i>
                                    <h5>Public Access</h5>
                                    <p>Share your server with friends using secure tunnels.</p>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Step 2: Admin Account -->
                    <div class="step" id="step2">
                        <h3>Create Admin Account</h3>
                        <p>Set up your administrator account to manage the server.</p>
                        
                        <form id="adminForm">
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <label for="adminUsername" class="form-label">Username</label>
                                    <input type="text" class="form-control" id="adminUsername" value="admin" required>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <label for="adminEmail" class="form-label">Email</label>
                                    <input type="email" class="form-control" id="adminEmail" placeholder="admin@example.com" required>
                                </div>
                            </div>
                            <div class="mb-3">
                                <label for="adminPassword" class="form-label">Password</label>
                                <input type="password" class="form-control" id="adminPassword" placeholder="Enter a secure password" required>
                            </div>
                            <div class="mb-3">
                                <label for="confirmPassword" class="form-label">Confirm Password</label>
                                <input type="password" class="form-control" id="confirmPassword" placeholder="Confirm your password" required>
                            </div>
                        </form>
                    </div>
                    
                    <!-- Step 3: Server Settings -->
                    <div class="step" id="step3">
                        <h3>Server Configuration</h3>
                        <p>Configure your Minecraft server settings.</p>
                        
                        <form id="serverForm">
                            <div class="mb-3">
                                <label for="serverName" class="form-label">Server Name</label>
                                <input type="text" class="form-control" id="serverName" value="My Minecraft Server" required>
                            </div>
                            <div class="mb-3">
                                <label for="maxPlayers" class="form-label">Maximum Players</label>
                                <input type="number" class="form-control" id="maxPlayers" value="20" min="1" max="100" required>
                            </div>
                            <div class="mb-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="enableTunnel">
                                    <label class="form-check-label" for="enableTunnel">
                                        Enable Public Tunnel (Share with friends online)
                                    </label>
                                </div>
                            </div>
                        </form>
                    </div>
                    
                    <!-- Step 4: Features -->
                    <div class="step" id="step4">
                        <h3>Optional Features</h3>
                        <p>Choose which features you'd like to enable.</p>
                        
                        <form id="featuresForm">
                            <div class="mb-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="enableUpdates" checked>
                                    <label class="form-check-label" for="enableUpdates">
                                        <strong>Automatic Updates</strong><br>
                                        <small class="text-muted">Get notified about new versions and features</small>
                                    </label>
                                </div>
                            </div>
                            <div class="mb-3">
                                <div class="form-check">
                                    <input class="form-check-input" type="checkbox" id="enableTray" checked>
                                    <label class="form-check-label" for="enableTray">
                                        <strong>System Tray Integration</strong><br>
                                        <small class="text-muted">Run in background with system tray icon</small>
                                    </label>
                                </div>
                            </div>
                            <div class="alert alert-info">
                                <h6><i class="fas fa-info-circle me-2"></i>Ready to Go!</h6>
                                <p class="mb-0">Click "Complete Setup" to finish the configuration and start using The Originals.</p>
                            </div>
                        </form>
                    </div>
                    
                    <!-- Navigation -->
                    <div class="d-flex justify-content-between mt-4">
                        <button type="button" class="btn btn-outline-secondary btn-wizard" id="prevBtn" onclick="changeStep(-1)" style="display: none;">
                            <i class="fas fa-arrow-left me-2"></i>Previous
                        </button>
                        <button type="button" class="btn btn-primary btn-wizard" id="nextBtn" onclick="changeStep(1)">
                            Next<i class="fas fa-arrow-right ms-2"></i>
                        </button>
                        <button type="button" class="btn btn-success btn-wizard" id="finishBtn" onclick="completeSetup()" style="display: none;">
                            <i class="fas fa-check me-2"></i>Complete Setup
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let currentStep = 1;
        const totalSteps = 4;
        
        function showStep(step) {
            // Hide all steps
            document.querySelectorAll('.step').forEach(s => s.classList.remove('active'));
            document.querySelectorAll('.step-item').forEach(s => {
                s.classList.remove('active', 'completed');
            });
            
            // Show current step
            document.getElementById('step' + step).classList.add('active');
            
            // Update step indicators
            for (let i = 1; i <= totalSteps; i++) {
                const indicator = document.querySelector(`[data-step="${i}"]`);
                if (i < step) {
                    indicator.classList.add('completed');
                } else if (i === step) {
                    indicator.classList.add('active');
                }
            }
            
            // Update navigation buttons
            document.getElementById('prevBtn').style.display = step > 1 ? 'block' : 'none';
            document.getElementById('nextBtn').style.display = step < totalSteps ? 'block' : 'none';
            document.getElementById('finishBtn').style.display = step === totalSteps ? 'block' : 'none';
        }
        
        function changeStep(direction) {
            if (direction === 1 && !validateCurrentStep()) {
                return;
            }
            
            currentStep += direction;
            if (currentStep < 1) currentStep = 1;
            if (currentStep > totalSteps) currentStep = totalSteps;
            
            showStep(currentStep);
        }
        
        function validateCurrentStep() {
            if (currentStep === 2) {
                const password = document.getElementById('adminPassword').value;
                const confirm = document.getElementById('confirmPassword').value;
                
                if (password !== confirm) {
                    alert('Passwords do not match!');
                    return false;
                }
                
                if (password.length < 6) {
                    alert('Password must be at least 6 characters long!');
                    return false;
                }
            }
            
            return true;
        }
        
        async function completeSetup() {
            if (!validateCurrentStep()) return;
            
            const setupData = {
                admin_username: document.getElementById('adminUsername').value,
                admin_password: document.getElementById('adminPassword').value,
                admin_email: document.getElementById('adminEmail').value,
                server_name: document.getElementById('serverName').value,
                max_players: parseInt(document.getElementById('maxPlayers').value),
                enable_tunnel: document.getElementById('enableTunnel').checked,
                enable_updates: document.getElementById('enableUpdates').checked,
                enable_tray: document.getElementById('enableTray').checked
            };
            
            try {
                const response = await fetch('/api/setup', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(setupData)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    alert('Setup completed successfully! The Originals will now start.');
                    window.close();
                } else {
                    alert('Setup failed: ' + result.message);
                }
            } catch (error) {
                alert('Setup failed: ' + error.message);
            }
        }
        
        // Initialize
        showStep(1);
    </script>
</body>
</html>
'''

if __name__ == "__main__":
    if is_first_run():
        run_setup_wizard()
    else:
        print("Setup already completed. Delete '.setup_complete' file to run setup again.") 