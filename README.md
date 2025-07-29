# 🚀 Quick Transfer Pro - Secure Real-time File Sharing

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/mr-singh-7112/filetransfer)

A **production-grade, secure** file transfer system with advanced encryption, owner authentication, and modern web interface. Built for privacy and security while maintaining simplicity.

🔐 **Security First**: File encryption, owner tokens, secure deletion, automatic cleanup
🌟 **Perfect for**: Secure file sharing, avoiding cloud storage, transferring large files (up to 5GB), private document sharing

## 🚀 Live Demo

**Try it now**: [https://your-app-name.herokuapp.com](https://your-app-name.herokuapp.com) _(Will be updated after deployment)_

## 🔐 Security Features

- 🔑 **Owner Authentication**: Only file uploaders can delete their files using secure tokens
- 🔒 **File Encryption**: All uploaded files are encrypted using Fernet symmetric encryption
- 🎩 **Secure Tokens**: Each file has a unique owner token stored securely in browser
- 🖪 **Session Isolation**: Users can only manage files they uploaded
- ⏰ **Auto-Cleanup**: Files and tokens are automatically deleted after 24 hours
- 🛮 **Privacy First**: No personal data stored, no account creation required

## ✨ Features

- 📱 **Mobile-First Design**: Beautiful, responsive interface optimized for phones
- ⚡ **Lightning Fast**: Direct network transfer with real-time progress
- 🚀 **Large File Support**: Handle files up to 5GB
- 🔒 **No Login Required**: No accounts, no WhatsApp Web, just upload and go!
- 📊 **Progress Tracking**: See upload progress in real-time
- 📁 **Instant Access**: Files immediately available on your computer
- 🎨 **Beautiful UI**: Clean, modern design with drag & drop support
- 🌐 **Cross-Platform**: Works on any device with a web browser
- 📱 **PWA Support**: Install as mobile app for offline usage

## 🚀 How to Use

### Step 1: Start the Server
Double-click `start.sh` or run in terminal:
```bash
./start.sh
```

### Step 2: Connect Your Phone
1. Make sure your phone and computer are on the same WiFi network
2. The server will show you an IP address like: `http://192.168.1.100:8080`
3. Open this address in your phone's browser
4. You'll see a beautiful upload interface!

### Step 3: Transfer Files
- **From Phone**: Tap the upload area or drag & drop files
- **To Computer**: Files are automatically saved in the `uploads` folder
- **Download**: Click the download button for any file

## ✨ Features

- ⚡ **Super Fast**: Direct local network transfer (no internet needed!)
- 📱 **Mobile Friendly**: Works perfectly on phone browsers
- 🔒 **No Login Required**: No WhatsApp, no accounts, no hassle
- 📊 **Progress Tracking**: See upload progress in real-time
- 📁 **File Management**: View and download all transferred files
- 🚀 **Large Files**: Supports up to 5GB per file
- 🎨 **Beautiful Interface**: Clean, modern design

## 🔧 Technical Details

- Built with Python 3 + cryptography library for encryption
- Runs on port 8081 by default (configurable via PORT env var)
- Files encrypted and saved in `uploads/` folder
- Owner tokens stored as `.token` files for authentication
- Supports all file types with automatic encryption/decryption
- Thread-safe for multiple simultaneous uploads
- Real-time file cleanup every hour for expired files
- PWA manifest for mobile app installation

## 🛠️ Troubleshooting

**Can't access from phone?**
- Make sure both devices are on the same WiFi
- Check if firewall is blocking port 8080
- Try using the computer's IP address manually

**Server won't start?**
- Make sure Python 3 is installed
- Try running `python3 server.py` directly

**Upload fails?**
- Check available disk space
- Make sure file isn't corrupted
- Try smaller files first

## 🎯 Perfect For

- Sending photos/videos from phone to computer
- Transferring documents quickly  
- Sharing large files locally
- Avoiding cloud storage limits
- Working offline

---

**No more WhatsApp Web login hassles! 🎉**
