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
echo "⬆️ Upgrading pip, setuptools, wheel..."
$VENV/pip install --upgrade pip setuptools wheel

# Clear old NumPy and Pandas to avoid binary incompatibility
echo "🧹 Removing old NumPy and Pandas..."
$VENV/pip uninstall -y numpy pandas

# Clear pip cache to avoid old wheels
echo "🗑️ Clearing pip cache..."
$VENV/pip cache purge || true

# Install compatible NumPy and Pandas
echo "🔧 Installing compatible NumPy and Pandas..."
$VENV/pip install --no-cache-dir numpy==2.3.3
$VENV/pip install --no-cache-dir pandas==2.1.1

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
