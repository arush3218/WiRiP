#!/bin/bash

# WiRiP Blog Startup Script
# This script helps you start the blog in development mode

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎵 Starting WiRiP Blog...${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python -m venv venv
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows
    source venv/Scripts/activate
else
    # Unix/Linux/macOS
    source venv/bin/activate
fi

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}Please update the .env file with your configuration${NC}"
fi

# Initialize database if it doesn't exist
if [ ! -f "wirip.db" ]; then
    echo -e "${BLUE}Initializing database...${NC}"
    python -c "
from app import app, db, init_db
init_db()
print('Database initialized successfully!')
"
fi

echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo -e "${BLUE}📋 Quick Start:${NC}"
echo "   🌐 The blog will be available at: http://localhost:5000"
echo "   👤 Default admin login: admin / admin123"
echo "   ⚠️  Change the admin password after first login!"
echo ""
echo -e "${BLUE}Starting the development server...${NC}"

# Start the application
python app.py