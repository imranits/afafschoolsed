#!/bin/bash

# Simple Auto Deploy Script for Afaq School Application
# Run this on your VPS to update from GitHub

set -e

APP_DIR="/var/www/afaqschool"
SERVICE_NAME="afaqschool"

echo "🚀 Updating Afaq School Application..."

cd $APP_DIR

# Pull latest changes safely
echo "📥 Pulling latest changes from GitHub..."
git fetch origin main
git reset --hard origin/main

# Update dependencies
echo "📦 Updating Python dependencies..."
$APP_DIR/venv/bin/pip install -r requirements.txt

# Set permissions
echo "🔐 Setting permissions..."
chown -R www-data:www-data $APP_DIR
chmod -R 755 $APP_DIR
chmod -R 775 $APP_DIR/static/uploads
chmod -R 775 $APP_DIR/static/receipts

# Restart service
echo "🔄 Restarting service..."
systemctl restart $SERVICE_NAME

echo "✅ Update completed successfully!"
