#!/bin/bash

# Upload Afaq School Application to VPS
# Usage: ./upload_to_vps.sh your_vps_ip

if [ $# -eq 0 ]; then
    echo "Usage: ./upload_to_vps.sh <VPS_IP_ADDRESS>"
    echo "Example: ./upload_to_vps.sh 192.168.1.100"
    exit 1
fi

VPS_IP=$1
VPS_USER="root"

echo "🚀 Uploading Afaq School Application to VPS at $VPS_IP..."

# Create deployment directory on VPS
echo "Creating deployment directory on VPS..."
ssh $VPS_USER@$VPS_IP "mkdir -p /tmp/afaqschool_deployment"

# Upload all necessary files
echo "Uploading application files..."
scp -r app.py $VPS_USER@$VPS_IP:/tmp/afaqschool_deployment/
scp -r app_production.py $VPS_USER@$VPS_IP:/tmp/afaqschool_deployment/
scp -r templates/ $VPS_USER@$VPS_IP:/tmp/afaqschool_deployment/
scp -r static/ $VPS_USER@$VPS_IP:/tmp/afaqschool_deployment/
scp requirements.txt $VPS_USER@$VPS_IP:/tmp/afaqschool_deployment/
scp afaqschool.sql $VPS_USER@$VPS_IP:/tmp/afaqschool_deployment/
scp deploy.sh $VPS_USER@$VPS_IP:/tmp/afaqschool_deployment/
scp afaqschool.service $VPS_USER@$VPS_IP:/tmp/afaqschool_deployment/
scp nginx.conf $VPS_USER@$VPS_IP:/tmp/afaqschool_deployment/
scp env.example $VPS_USER@$VPS_IP:/tmp/afaqschool_deployment/
scp setup_database.sql $VPS_USER@$VPS_IP:/tmp/afaqschool_deployment/
scp DEPLOYMENT_GUIDE.md $VPS_USER@$VPS_IP:/tmp/afaqschool_deployment/

echo "✅ Files uploaded successfully!"
echo ""
echo "Next steps on your VPS:"
echo "1. cd /tmp/afaqschool_deployment"
echo "2. chmod +x deploy.sh"
echo "3. sudo ./deploy.sh"
echo ""
echo "Or run the manual deployment steps from DEPLOYMENT_GUIDE.md"
