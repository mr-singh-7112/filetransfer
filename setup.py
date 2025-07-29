#!/usr/bin/env python3
"""
Quick File Transfer - Cross-Platform Setup
Automatically detects OS and sets up the file transfer system
"""

import os
import sys
import platform
import subprocess

def check_python():
    """Check if Python 3 is available"""
    version = sys.version_info
    if version.major < 3:
        print("❌ Python 3 is required. Please install Python 3.")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def create_desktop_shortcut():
    """Create desktop shortcut based on OS"""
    system = platform.system().lower()
    
    if system == "windows":
        # Windows shortcut
        shortcut_content = f"""@echo off
cd /d "{os.getcwd()}"
python server.py
pause"""
        with open("Quick File Transfer.bat", "w") as f:
            f.write(shortcut_content)
        print("✅ Created 'Quick File Transfer.bat' - double-click to start!")
    
    elif system == "darwin":  # macOS
        # macOS app bundle or script
        app_script = f"""#!/bin/bash
cd "{os.getcwd()}"
python3 server.py"""
        with open("Quick File Transfer.command", "w") as f:
            f.write(app_script)
        os.chmod("Quick File Transfer.command", 0o755)
        print("✅ Created 'Quick File Transfer.command' - double-click to start!")
    
    elif system == "linux":
        # Linux desktop entry
        desktop_entry = f"""[Desktop Entry]
Name=Quick File Transfer
Comment=Transfer files between phone and computer
Exec=python3 "{os.path.join(os.getcwd(), 'server.py')}"
Icon=folder
Terminal=true
Type=Application
Categories=Network;FileTransfer;"""
        
        desktop_path = os.path.expanduser("~/Desktop/Quick File Transfer.desktop")
        with open(desktop_path, "w") as f:
            f.write(desktop_entry)
        os.chmod(desktop_path, 0o755)
        print("✅ Created desktop shortcut!")

def main():
    print("🚀 Quick File Transfer - Setup")
    print("=" * 40)
    
    # Check Python
    if not check_python():
        return
    
    # Detect OS
    system = platform.system()
    print(f"💻 Operating System: {system}")
    
    # Create uploads directory
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
        print("✅ Created uploads directory")
    
    # Create shortcut
    create_desktop_shortcut()
    
    print("\n" + "=" * 40)
    print("🎉 Setup Complete!")
    print("\n📱 Usage:")
    print("1. Run the server (double-click the shortcut or run 'python3 server.py')")
    print("2. Connect your phone to the same WiFi")
    print("3. Open your phone's browser to the displayed IP address")
    print("4. Start transferring files!")
    print("\n✨ No login required - just fast, local file transfers!")

if __name__ == "__main__":
    main()
