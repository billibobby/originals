#!/usr/bin/env python3
"""
Test script for The Originals Auto-Update System
This script demonstrates the new update features and tests functionality.
"""

import requests
import json
import time
import sys
from datetime import datetime

def test_update_system():
    """Test the enhanced auto-update system"""
    
    print("=" * 60)
    print("🚀 The Originals - Auto-Update System Test")
    print("=" * 60)
    
    base_url = "http://localhost:3000"
    
    # Test 1: Check for Updates
    print("\n1. Testing Update Check...")
    try:
        response = requests.get(f"{base_url}/api/updates/check?force=true")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Update check successful")
            print(f"   📦 Current version: {result.get('current_version', 'Unknown')}")
            print(f"   🔄 Latest version: {result.get('latest_version', 'Unknown')}")
            print(f"   🆕 Update available: {result.get('update_available', False)}")
        else:
            print(f"   ❌ Update check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Get Update Status
    print("\n2. Testing Update Status...")
    try:
        response = requests.get(f"{base_url}/api/updates/status")
        if response.status_code == 200:
            status = response.json()
            print(f"   ✅ Status retrieved successfully")
            print(f"   ⏰ Background running: {status.get('background_running', False)}")
            print(f"   ⏱️ Check interval: {status.get('check_interval', 0)} seconds")
            print(f"   🕒 Last check: {status.get('last_check', 'Never')}")
            print(f"   🔑 Trigger keywords: {', '.join(status.get('manual_keywords', []))}")
        else:
            print(f"   ❌ Status check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Manual Trigger
    print("\n3. Testing Manual Trigger...")
    try:
        trigger_texts = [
            "time to update",
            "check for updates",
            "update now",
            "new version"
        ]
        
        for text in trigger_texts:
            response = requests.post(f"{base_url}/api/updates/trigger", 
                                   json={"text": text},
                                   headers={"Content-Type": "application/json"})
            if response.status_code == 200:
                result = response.json()
                if result.get('triggered'):
                    print(f"   ✅ Trigger '{text}' works!")
                else:
                    print(f"   ⚠️ Trigger '{text}' not recognized")
            else:
                print(f"   ❌ Trigger test failed: {response.status_code}")
            time.sleep(1)  # Avoid rate limiting
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Configuration
    print("\n4. Testing Configuration...")
    try:
        response = requests.get(f"{base_url}/api/updates/config")
        if response.status_code == 200:
            config = response.json()
            print(f"   ✅ Configuration retrieved")
            print(f"   ⏰ Check interval: {config.get('check_interval', 0)} seconds")
            print(f"   🏃 Background running: {config.get('background_running', False)}")
            print(f"   🔑 Manual keywords: {len(config.get('manual_keywords', []))} keywords")
        else:
            print(f"   ❌ Configuration check failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Server Health Check
    print("\n5. Testing Server Health...")
    try:
        response = requests.get(f"{base_url}/api/server/status")
        if response.status_code == 200:
            print(f"   ✅ Server is running and responsive")
        else:
            print(f"   ⚠️ Server responded but may have issues: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Server not reachable: {e}")
    
    print("\n" + "=" * 60)
    print("🎉 Auto-Update System Test Complete!")
    print("=" * 60)
    
    print("\n📋 How to Use the New Features:")
    print("1. The system checks for updates every hour automatically")
    print("2. Click your username → 'Check for Updates' for manual check")
    print("3. Type 'time to update' in any command box to trigger check")
    print("4. Updates will show beautiful notifications with progress")
    print("5. All updates are secure with checksum verification")
    
    print("\n🔮 Manual Trigger Keywords:")
    print("- 'time to update' - Triggers update check")
    print("- 'update now' - Triggers update check")
    print("- 'check for updates' - Triggers update check")
    print("- 'new version' - Triggers update check")
    
    print("\n🛡️ Security Features:")
    print("- SHA256 checksum verification")
    print("- Automatic backup before updates")
    print("- Secure download from GitHub releases")
    print("- Error recovery and rollback")
    
    print("\n🎯 Next Steps:")
    print("1. Start your Minecraft server management app")
    print("2. Try typing 'time to update' in the command box")
    print("3. Check the user menu for 'Check for Updates'")
    print("4. Watch for automatic hourly update checks")
    
    print("\n💝 Enjoy your enhanced auto-update experience!")

if __name__ == "__main__":
    test_update_system() 