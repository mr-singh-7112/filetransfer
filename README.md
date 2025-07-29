# 📱➡️💻 Quick File Transfer

A super simple local file transfer solution to send files from your phone to your computer without needing WhatsApp Web login!

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

- Built with Python 3 (uses only standard libraries)
- Runs on port 8080 by default
- Files saved in `uploads/` folder
- Supports all file types
- Thread-safe for multiple simultaneous uploads

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
