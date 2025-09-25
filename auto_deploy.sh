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

# Reinstall numpy + pandas together
echo "📦 Reinstalling numpy and pandas safely..."
$VENV/pip install --upgrade --force-reinstall numpy==2.3.3 pandas==2.1.1

# Install other dependencies without touching numpy/pandas
echo "📦 Installing other Python dependencies..."
$VENV/pip install --upgrade -r requirements.txt --no-deps


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
