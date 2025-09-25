#!/bin/bash
set -e

APP_DIR="/var/www/afaqschool"
SERVICE_NAME="afaqschool"
VENV="$APP_DIR/venv/bin"

echo "🚀 Updating Afaq School Application..."
cd $APP_DIR

# Stop service first
echo "💀 Stopping Gunicorn service..."
systemctl stop $SERVICE_NAME || true

# Pull latest changes
echo "📥 Pulling latest changes from GitHub..."
git fetch origin main
git reset --hard origin/main

# Upgrade pip
echo "⬆️  Upgrading pip..."
$VENV/pip install --upgrade pip setuptools wheel

# Clean uninstall first hanan
$VENV/pip uninstall -y numpy pandas

# Install compatible numpy first
$VENV/pip install numpy==2.3.3

# Then install pandas
$VENV/pip install pandas==2.1.1

# Now install remaining requirements WITHOUT upgrading numpy/pandas
$VENV/pip install --upgrade --no-deps -r requirements.txt



# Set permissions
echo "🔐 Setting permissions..."
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR
chmod -R 775 $APP_DIR/static/uploads
chmod -R 775 $APP_DIR/static/receipts

# Restart Gunicorn service
echo "🔄 Restarting service..."
systemctl daemon-reload
systemctl start $SERVICE_NAME

echo "✅ Update completed successfully!"
