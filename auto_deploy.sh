#!/bin/bash
set -e

APP_DIR="/var/www/afaqschool"
SERVICE_NAME="afaqschool"
VENV="$APP_DIR/venv/bin"

echo "🚀 Updating Afaq School Application..."
cd $APP_DIR

# Stop systemd service first (if running)
echo "💀 Stopping Gunicorn service..."
systemctl stop $SERVICE_NAME || true

# Kill any remaining Gunicorn processes manually
echo "⚔️ Killing any leftover Gunicorn processes..."
pkill -f "gunicorn" || true

# Verify no Gunicorn processes are running
echo "🔍 Verifying Gunicorn processes..."
pgrep -fl gunicorn || echo "No Gunicorn processes running."

# Pull latest changes
echo "📥 Pulling latest changes from GitHub..."
git fetch origin main
git reset --hard origin/main

# Upgrade pip, setuptools, and wheel
echo "⬆️ Upgrading pip, setuptools, and wheel..."
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

# Start Gunicorn manually (instead of systemctl) in background
echo "🚀 Starting Gunicorn..."
$VENV/gunicorn -w 4 -b 127.0.0.1:8000 app:app &

echo "✅ Update completed successfully!"
