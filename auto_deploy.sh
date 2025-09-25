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

# Upgrade pip, setuptools, and wheel
echo "⬆️  Upgrading pip, setuptools, and wheel..."
$VENV/pip install --upgrade pip setuptools wheel

# Reinstall numpy and pandas cleanly
echo "🔄 Reinstalling numpy and pandas..."
$VENV/pip uninstall -y numpy pandas
$VENV/pip install numpy pandas

# Clear any compiled caches
echo "🧹 Clearing Python bytecode caches..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# Install the rest of the requirements without touching numpy/pandas
echo "📦 Installing remaining requirements..."
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
