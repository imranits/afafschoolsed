# 🚀 Simple Deployment Guide

## What You Actually Need

### 1. **Your VPS Setup** (One-time)
```bash
# On your VPS, run:
cd /var/www/afaqschool
sudo ./auto_deploy.sh
```

### 2. **Your Daily Workflow**
```bash
# 1. Make changes locally
# 2. Test your changes
# 3. Push to GitHub
git add .
git commit -m "Your changes"
git push origin main

# 4. SSH to VPS and update
ssh root@your-vps-ip
cd /var/www/afaqschool
sudo ./auto_deploy.sh
```

### 3. **That's It!**

Your app will be updated with the latest changes. The script:
- Pulls latest code from GitHub
- Updates Python dependencies
- Sets proper permissions
- Restarts the service

## Files You Need:
- ✅ `auto_deploy.sh` - Simple update script
- ✅ `app.py` - Your main application
- ✅ `requirements.txt` - Python dependencies
- ✅ `afaqschool.service` - System service
- ✅ `nginx.conf` - Web server config

## Optional: GitHub Webhook (Advanced)
If you want automatic deployment without SSH:
1. Set up a webhook on GitHub pointing to your VPS
2. Create a simple webhook receiver
3. But honestly, the manual way above is simpler and more reliable
