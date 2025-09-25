#!/bin/bash

# Update Afaq School Application from GitHub
# Run this script on your VPS to update the application

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run this script as root or with sudo"
    exit 1
fi

print_status "🔄 Updating Afaq School Application from GitHub..."

# Navigate to application directory
cd /var/www/afaqschool

# Backup current version
print_status "Creating backup..."
cp -r . ../afaqschool_backup_$(date +%Y%m%d_%H%M%S)

# Pull latest changes
print_status "Pulling latest changes from GitHub..."
git pull origin main

# Update Python dependencies
print_status "Updating Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt

# Set proper permissions
print_status "Setting proper permissions..."
chown -R www-data:www-data /var/www/afaqschool
chmod -R 755 /var/www/afaqschool
chmod -R 777 /var/www/afaqschool/static/uploads
chmod -R 777 /var/www/afaqschool/static/receipts

# Restart services
print_status "Restarting services..."
systemctl restart afaqschool
systemctl restart nginx

print_status "✅ Application updated successfully!"
print_warning "Check the application at http://your-server-ip"
