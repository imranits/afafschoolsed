#!/bin/bash

# Afaq School Application Deployment Script
# Run this script on your Ubuntu VPS as root or with sudo

set -e  # Exit on any error

echo "🚀 Starting Afaq School Application Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_error "Please run this script as root or with sudo"
    exit 1
fi

# Update system
print_status "Updating system packages..."
apt update && apt upgrade -y

# Install required packages
print_status "Installing required packages..."
apt install -y python3 python3-pip python3-venv nginx mysql-server git curl wget

# Configure firewall
print_status "Configuring firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

# Start and enable MySQL
print_status "Starting MySQL service..."
systemctl start mysql
systemctl enable mysql

# Secure MySQL installation
print_warning "You will be prompted to secure MySQL installation..."
mysql_secure_installation

# Create application directory
print_status "Creating application directory..."
mkdir -p /var/www/afaqschool
chown -R www-data:www-data /var/www/afaqschool

# Create virtual environment
print_status "Setting up Python virtual environment..."
cd /var/www/afaqschool
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
print_status "Creating upload directories..."
mkdir -p static/uploads
mkdir -p static/receipts
chown -R www-data:www-data static/
chmod -R 755 static/

# Set up environment file
print_status "Setting up environment configuration..."
if [ ! -f .env ]; then
    cp env.example .env
    print_warning "Please edit /var/www/afaqschool/.env with your actual configuration values"
fi

# Copy systemd service file
print_status "Setting up systemd service..."
cp afaqschool.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable afaqschool

# Copy Nginx configuration
print_status "Setting up Nginx configuration..."
cp nginx.conf /etc/nginx/sites-available/afaqschool
ln -sf /etc/nginx/sites-available/afaqschool /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
print_status "Testing Nginx configuration..."
nginx -t

# Restart services
print_status "Restarting services..."
systemctl restart nginx
systemctl start afaqschool

# Set proper permissions
print_status "Setting proper permissions..."
chown -R www-data:www-data /var/www/afaqschool
chmod -R 755 /var/www/afaqschool
chmod -R 777 /var/www/afaqschool/static/uploads
chmod -R 777 /var/www/afaqschool/static/receipts

# Create backup directory
print_status "Creating backup directory..."
mkdir -p /var/backups
chown www-data:www-data /var/backups

print_status "✅ Deployment completed successfully!"
print_warning "Next steps:"
echo "1. Edit /var/www/afaqschool/.env with your database credentials"
echo "2. Import your database schema: mysql -u root -p afaqschool1 < afaqschool.sql"
echo "3. Update Nginx configuration with your domain name"
echo "4. Test your application at http://your-server-ip"
echo "5. Consider setting up SSL certificate with Let's Encrypt"

print_status "Useful commands:"
echo "- Check service status: systemctl status afaqschool"
echo "- View logs: journalctl -u afaqschool -f"
echo "- Restart service: systemctl restart afaqschool"
