#!/bin/bash

# WiRiP Blog Deployment Script for AWS EC2
# This script automates the deployment process on Ubuntu Server

set -e  # Exit on any error

echo "🎵 Starting WiRiP Blog Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    print_error "Please don't run this script as root"
    exit 1
fi

# Update system
print_status "Updating system packages..."
sudo apt update && sudo apt upgrade -y
print_success "System updated successfully"

# Install dependencies
print_status "Installing system dependencies..."
sudo apt install -y python3 python3-pip python3-venv nginx git ufw
print_success "Dependencies installed"

# Configure firewall
print_status "Configuring firewall..."
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
print_success "Firewall configured"

# Get project directory
PROJECT_DIR="/home/$USER/wirip-blog"

# Clone or update repository
if [ -d "$PROJECT_DIR" ]; then
    print_status "Updating existing repository..."
    cd "$PROJECT_DIR"
    git pull origin main
else
    print_status "Cloning repository..."
    git clone https://github.com/your-username/wirip-blog.git "$PROJECT_DIR"
    cd "$PROJECT_DIR"
fi

# Set up virtual environment
print_status "Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
print_success "Virtual environment ready"

# Initialize database
print_status "Initializing database..."
python app.py &
sleep 5
pkill -f "python app.py"
print_success "Database initialized"

# Create Gunicorn service
print_status "Creating Gunicorn service..."
sudo tee /etc/systemd/system/wirip.service > /dev/null <<EOF
[Unit]
Description=Gunicorn instance to serve WiRiP Blog
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --workers 3 --bind unix:wirip.sock -m 007 app:app
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl start wirip
sudo systemctl enable wirip
print_success "Gunicorn service created and started"

# Configure Nginx
print_status "Configuring Nginx..."
sudo tee /etc/nginx/sites-available/wirip > /dev/null <<EOF
server {
    listen 80;
    server_name _;

    location / {
        include proxy_params;
        proxy_pass http://unix:$PROJECT_DIR/wirip.sock;
    }

    location /static {
        alias $PROJECT_DIR/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
}
EOF

# Remove default Nginx site
sudo rm -f /etc/nginx/sites-enabled/default

# Enable WiRiP site
sudo ln -sf /etc/nginx/sites-available/wirip /etc/nginx/sites-enabled/

# Test Nginx configuration
if sudo nginx -t; then
    sudo systemctl restart nginx
    print_success "Nginx configured and restarted"
else
    print_error "Nginx configuration test failed"
    exit 1
fi

# Create update script
print_status "Creating update script..."
tee "$PROJECT_DIR/update.sh" > /dev/null <<EOF
#!/bin/bash
# WiRiP Blog Update Script

cd $PROJECT_DIR
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart wirip
sudo systemctl reload nginx

echo "✅ WiRiP Blog updated successfully!"
EOF

chmod +x "$PROJECT_DIR/update.sh"
print_success "Update script created"

# Get server IP
SERVER_IP=$(curl -s http://checkip.amazonaws.com/)

print_success "🎉 WiRiP Blog deployment completed!"
echo ""
echo "📋 Deployment Summary:"
echo "   📁 Project Directory: $PROJECT_DIR"
echo "   🌐 Server IP: $SERVER_IP"
echo "   🔗 Access your blog at: http://$SERVER_IP"
echo ""
echo "👤 Default Admin Credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo "   ⚠️  IMPORTANT: Change this password after first login!"
echo ""
echo "🔧 Useful Commands:"
echo "   Check service status: sudo systemctl status wirip"
echo "   View logs: sudo journalctl -u wirip -f"
echo "   Restart service: sudo systemctl restart wirip"
echo "   Update blog: $PROJECT_DIR/update.sh"
echo ""
echo "🔒 SSL Certificate (Optional):"
echo "   Install: sudo apt install certbot python3-certbot-nginx"
echo "   Get certificate: sudo certbot --nginx -d yourdomain.com"
echo ""

# Check if services are running
if systemctl is-active --quiet wirip && systemctl is-active --quiet nginx; then
    print_success "All services are running successfully!"
    echo "🎵 Your WiRiP blog is now live at http://$SERVER_IP"
else
    print_warning "Some services may not be running properly. Please check the logs."
fi

print_status "Deployment script completed!"