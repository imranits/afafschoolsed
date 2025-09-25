#!/bin/bash

# Quick setup script to run on VPS
# This will create all necessary files directly on the VPS

echo "🚀 Setting up Afaq School Application on VPS..."

# Update system
echo "Updating system..."
apt update && apt upgrade -y

# Install required packages
echo "Installing required packages..."
apt install -y python3 python3-pip python3-venv nginx mysql-server git curl wget

# Create application directory
echo "Creating application directory..."
mkdir -p /var/www/afaqschool
cd /var/www/afaqschool

# Create requirements.txt
echo "Creating requirements.txt..."
cat > requirements.txt << 'EOF'
Flask==2.3.3
mysql-connector-python==8.1.0
Werkzeug==2.3.7
pandas==2.1.1
openpyxl==3.1.2
python-dotenv==1.0.0
gunicorn==21.2.0
EOF

# Create environment file
echo "Creating environment configuration..."
cat > .env << 'EOF'
DB_HOST=localhost
DB_PORT=3306
DB_USER=afaqschool_user
DB_PASS=SecurePassword123!
DB_NAME=afaqschool1
SECRET_KEY=your_super_secret_key_change_this_in_production
FLASK_ENV=production
FLASK_DEBUG=False
ADMIN_PASSWORD=admin12345
UPLOAD_FOLDER=static/uploads
RECEIPT_FOLDER=static/receipts
EOF

# Create systemd service file
echo "Creating systemd service..."
cat > afaqschool.service << 'EOF'
[Unit]
Description=Afaq School Flask Application
After=network.target mysql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/afaqschool
Environment=PATH=/var/www/afaqschool/venv/bin
ExecStart=/var/www/afaqschool/venv/bin/gunicorn --workers 3 --bind unix:/var/www/afaqschool/afaqschool.sock -m 007 app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create Nginx configuration
echo "Creating Nginx configuration..."
cat > nginx.conf << 'EOF'
server {
    listen 80;
    server_name 72.60.198.152;  # Your VPS IP

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/afaqschool/afaqschool.sock;
    }

    location /static {
        alias /var/www/afaqschool/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    # File upload size limit
    client_max_body_size 10M;
}
EOF

# Create database setup script
echo "Creating database setup script..."
cat > setup_database.sql << 'EOF'
-- Create database and user for Afaq School application
CREATE DATABASE IF NOT EXISTS afaqschool1 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create a dedicated user for the application
CREATE USER IF NOT EXISTS 'afaqschool_user'@'localhost' IDENTIFIED BY 'SecurePassword123!';
GRANT ALL PRIVILEGES ON afaqschool1.* TO 'afaqschool_user'@'localhost';
FLUSH PRIVILEGES;

-- Use the database
USE afaqschool1;
EOF

echo "✅ Basic setup files created!"
echo ""
echo "Next steps:"
echo "1. You need to upload your app.py, templates/, and static/ folders"
echo "2. Run: mysql -u root -p < setup_database.sql"
echo "3. Then import your afaqschool.sql file"
echo "4. Set up the Python environment and start the service"
