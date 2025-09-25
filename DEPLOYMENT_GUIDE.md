# Afaq School Application - Ubuntu VPS Deployment Guide

This guide will help you deploy your Flask application on an Ubuntu VPS with proper database configuration, security, and production setup.

## Prerequisites

- Ubuntu 20.04+ VPS with root/sudo access
- Domain name pointing to your VPS IP (optional but recommended)
- Basic knowledge of Linux commands

## Step 1: Initial Server Setup

### 1.1 Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Install Essential Packages
```bash
sudo apt install -y python3 python3-pip python3-venv nginx mysql-server git curl wget
```

### 1.3 Configure Firewall
```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Step 2: Database Setup

### 2.1 Secure MySQL Installation
```bash
sudo mysql_secure_installation
```
Follow the prompts to set a root password and secure your installation.

### 2.2 Create Database and User
```bash
sudo mysql -u root -p
```

Run the following SQL commands:
```sql
CREATE DATABASE IF NOT EXISTS afaqschool1 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'afaqschool_user'@'localhost' IDENTIFIED BY 'your_secure_password_here';
GRANT ALL PRIVILEGES ON afaqschool1.* TO 'afaqschool_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 2.3 Import Your Database Schema
```bash
# Upload your afaqschool.sql file to the server first
mysql -u afaqschool_user -p afaqschool1 < /path/to/afaqschool.sql
```

## Step 3: Application Deployment

### 3.1 Create Application Directory
```bash
sudo mkdir -p /var/www/afaqschool
sudo chown -R $USER:$USER /var/www/afaqschool
cd /var/www/afaqschool
```

### 3.2 Upload Your Application Files
Upload all your application files to `/var/www/afaqschool/`:
- app.py
- templates/ (entire folder)
- static/ (entire folder)
- requirements.txt
- afaqschool.sql

### 3.3 Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.4 Configure Environment Variables
```bash
cp env.example .env
nano .env
```

Update the `.env` file with your actual values:
```
DB_HOST=localhost
DB_PORT=3306
DB_USER=afaqschool_user
DB_PASS=your_secure_password_here
DB_NAME=afaqschool1
SECRET_KEY=your_super_secret_key_here_change_this
FLASK_ENV=production
FLASK_DEBUG=False
ADMIN_PASSWORD=admin12345
UPLOAD_FOLDER=static/uploads
RECEIPT_FOLDER=static/receipts
```

### 3.5 Update app.py for Production
You need to modify your `app.py` to use environment variables:

```python
# Add this at the top of app.py after imports
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Update DB_CONFIG to use environment variables
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", "Zain12345"),
    "database": os.getenv("DB_NAME", "afaqschool1")
}

# Update other configurations
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin12345")
app.secret_key = os.getenv("SECRET_KEY", "supersecret123")
```

### 3.6 Test the Application
```bash
python3 app.py
```
Visit `http://your-server-ip:5000` to test. Stop the server with Ctrl+C.

## Step 4: Configure Gunicorn

### 4.1 Create Gunicorn Configuration
```bash
nano gunicorn.conf.py
```

Add the following content:
```python
bind = "unix:/var/www/afaqschool/afaqschool.sock"
workers = 3
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True
```

### 4.2 Test Gunicorn
```bash
gunicorn --config gunicorn.conf.py app:app
```

## Step 5: Configure Systemd Service

### 5.1 Create Service File
```bash
sudo cp afaqschool.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable afaqschool
sudo systemctl start afaqschool
sudo systemctl status afaqschool
```

## Step 6: Configure Nginx

### 6.1 Create Nginx Configuration
```bash
sudo cp nginx.conf /etc/nginx/sites-available/afaqschool
sudo ln -s /etc/nginx/sites-available/afaqschool /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
```

### 6.2 Update Nginx Configuration
Edit the configuration file:
```bash
sudo nano /etc/nginx/sites-available/afaqschool
```

Update the `server_name` with your actual domain or IP address.

### 6.3 Test and Restart Nginx
```bash
sudo nginx -t
sudo systemctl restart nginx
```

## Step 7: Set Proper Permissions

### 7.1 Set Directory Permissions
```bash
sudo chown -R www-data:www-data /var/www/afaqschool
sudo chmod -R 755 /var/www/afaqschool
sudo chmod -R 777 /var/www/afaqschool/static/uploads
sudo chmod -R 777 /var/www/afafschool/static/receipts
```

### 7.2 Create Upload Directories
```bash
mkdir -p /var/www/afaqschool/static/uploads
mkdir -p /var/www/afaqschool/static/receipts
sudo chown -R www-data:www-data /var/www/afaqschool/static
```

## Step 8: SSL Certificate (Optional but Recommended)

### 8.1 Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx -y
```

### 8.2 Get SSL Certificate
```bash
sudo certbot --nginx -d your-domain.com
```

## Step 9: Database Verification

### 9.1 Test Database Connection
Create a test script:
```bash
nano test_db.py
```

```python
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

try:
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASS", "Zain12345"),
        database=os.getenv("DB_NAME", "afaqschool1")
    )
    print("Database connection successful!")
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print("Tables in database:", tables)
    conn.close()
except Exception as e:
    print("Database connection failed:", e)
```

Run the test:
```bash
python3 test_db.py
```

## Step 10: Monitoring and Maintenance

### 10.1 Check Application Status
```bash
sudo systemctl status afaqschool
sudo systemctl status nginx
sudo systemctl status mysql
```

### 10.2 View Logs
```bash
sudo journalctl -u afaqschool -f
sudo tail -f /var/log/nginx/error.log
```

### 10.3 Backup Database
```bash
# Create backup script
nano backup_db.sh
```

```bash
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump -u afaqschool_user -p afaqschool1 > /var/backups/afaqschool_$DATE.sql
```

```bash
sudo mkdir -p /var/backups
sudo chmod +x backup_db.sh
```

## Troubleshooting

### Common Issues:

1. **Permission Denied Errors**
   ```bash
   sudo chown -R www-data:www-data /var/www/afaqschool
   sudo chmod -R 755 /var/www/afaqschool
   ```

2. **Database Connection Errors**
   - Check if MySQL is running: `sudo systemctl status mysql`
   - Verify credentials in `.env` file
   - Test connection with the test script

3. **Static Files Not Loading**
   - Check Nginx configuration
   - Verify file permissions
   - Check if static directory exists

4. **Application Not Starting**
   - Check logs: `sudo journalctl -u afaqschool -f`
   - Verify all dependencies are installed
   - Check if virtual environment is activated

### Useful Commands:

```bash
# Restart services
sudo systemctl restart afaqschool
sudo systemctl restart nginx

# Check service status
sudo systemctl status afaqschool
sudo systemctl status nginx
sudo systemctl status mysql

# View logs
sudo journalctl -u afaqschool -f
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Test configuration
sudo nginx -t
```

## Security Considerations

1. **Change default passwords** in the `.env` file
2. **Use strong database passwords**
3. **Enable firewall** and only open necessary ports
4. **Keep system updated** regularly
5. **Use SSL certificates** for HTTPS
6. **Regular backups** of database and files
7. **Monitor logs** for suspicious activity

## Performance Optimization

1. **Enable Gzip compression** in Nginx
2. **Set up database indexing** for better performance
3. **Configure caching** for static files
4. **Monitor resource usage** with `htop` or `top`

Your application should now be accessible at `http://your-domain.com` or `http://your-server-ip`!
