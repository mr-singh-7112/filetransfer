# 🚀 Deployment Guide - Quick File Transfer

## 🎯 One-Click Deploy Options

### 🟣 Heroku (Easiest)
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/mr-singh-7112/filetransfer)

**Steps:**
1. Click the button above
2. Create a Heroku account if needed
3. Enter app name (e.g., `my-file-transfer-app`)
4. Click "Deploy app"
5. Wait for deployment (2-3 minutes)
6. Click "View" to access your app!

### 🔵 Railway (Alternative)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/OHNl6q)

### 🟢 Render (Free)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

---

## 🛠️ Manual Deployment

### 📋 Prerequisites
- Git installed
- Python 3.7+ installed
- Heroku CLI installed (`brew install heroku`)

### 🔧 Heroku Manual Deploy

1. **Login to Heroku:**
   ```bash
   heroku login
   ```

2. **Create Heroku app:**
   ```bash
   heroku create your-app-name
   ```

3. **Deploy:**
   ```bash
   git push heroku main
   ```

4. **Open your app:**
   ```bash
   heroku open
   ```

### 🌐 Other Platforms

#### **Vercel (Serverless)**
```bash
npm i -g vercel
vercel --prod
```

#### **AWS EC2 (Advanced)**
```bash
# SSH into your EC2 instance
git clone https://github.com/mr-singh-7112/filetransfer.git
cd filetransfer
python3 server.py
```

#### **Digital Ocean Droplet**
```bash
# Similar to AWS EC2
git clone https://github.com/mr-singh-7112/filetransfer.git
cd filetransfer
python3 server.py
```

---

## 🔧 Environment Variables

Set these if needed:
- `PORT`: Server port (default: 8081)

---

## 📱 After Deployment

1. **Get your app URL** (e.g., `https://your-app.herokuapp.com`)
2. **Open on your phone** - bookmark it!
3. **Start uploading files** from your mobile
4. **Access files** from any computer via the same URL

---

## 🎯 Usage Examples

### 📸 From Phone:
- Open: `https://your-app.herokuapp.com`
- Tap upload area
- Select photos/videos
- Upload instantly!

### 💻 From Computer:
- Open same URL
- View all uploaded files
- Download with one click
- No WhatsApp Web needed!

---

## 🔒 Security Notes

- Files are publicly accessible via the URL
- For private use, consider password protection
- Files stored temporarily on server
- Consider file size limits of your hosting platform

---

## 🆘 Troubleshooting

### **Deployment Issues:**
- Check logs: `heroku logs --tail`
- Verify Python version in `runtime.txt`
- Ensure all files are committed to git

### **Upload Issues:**
- Check file size limits (Heroku: 500MB)
- Verify internet connection
- Try smaller files first

### **Access Issues:**
- Ensure app is running: `heroku ps`
- Check app URL is correct
- Try different browser

---

## 🎉 Success!

Your file transfer system is now live and accessible from anywhere!

**Share the URL** with yourself and bookmark it on your phone for instant file transfers without WhatsApp Web hassles!

---

**Need help?** Open an issue on GitHub: https://github.com/mr-singh-7112/filetransfer/issues
