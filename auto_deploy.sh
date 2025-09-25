#!/bin/bash

# Safe Auto Deploy Script for Afaq School Application
# Ensures numpy/pandas compatibility
# Run this on your VPS to update from GitHub

set -e

APP_DIR="/var/www/afaqschool"
SERVICE_NAME="afaqschool"
VENV="$APP_DIR/venv/bin"

echo "🚀 Updating Afaq School Application..."

cd $APP_DIR

# Pull latest changes safely
echo "📥 Pulling latest changes from GitHub..."
git fetch origin main
git reset --hard origin/main

# Upgrade pip first
echo "⬆️  Upgrading pip..."
$VENV/pip install --upgrade pip setuptools wheel

# Reinstall numpy and pandas safely to avoid binary incompatibility
echo "📦 Reinstalling numpy and pandas for compatibility..."
$VENV/pip install --upgrade --force-reinstall numpy==2.3.3
$VENV/pip install --upgrade --force-reinstall pandas==2.1.1

# Install other dependencies without touching numpy/pandas
echo "📦 Installing other Python dependencies..."
$VENV/pip install -r requirements.txt --no-deps

# Set permissions
echo "🔐 Setting permissions..."
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR
chmod -R 775 $APP_DIR/static/uploads
chmod -R 775 $APP_DIR/static/receipts

# Kill any lingering gunicorn processes
echo "💀 Stopping old Gunicorn processes..."
pkill -f gunicorn || true

# Reload systemd and restart service
echo "🔄 Restarting service..."
systemctl daemon-reload
systemctl restart $SERVICE_NAME

echo "✅ Update completed successfully!"
