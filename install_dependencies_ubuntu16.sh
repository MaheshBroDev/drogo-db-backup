#!/bin/bash

# Install dependencies for Ubuntu 16.04
# Run this with sudo if you need to install system packages

echo "=========================================="
echo "Installing Dependencies for Ubuntu 16.04"
echo "=========================================="

# Update package list
echo "Updating package list..."
sudo apt-get update

# Install Python 3 and pip
echo "Installing Python 3 and pip..."
sudo apt-get install -y python3 python3-pip python3-venv

# Install MySQL client tools
echo "Installing MySQL client..."
sudo apt-get install -y mysql-client

# Verify installations
echo ""
echo "Verifying installations..."
echo "Python 3: $(python3 --version)"
echo "pip3: $(pip3 --version)"

if command -v mysqldump &> /dev/null; then
    echo "mysqldump: $(mysqldump --version)"
else
    echo "mysqldump: Not found"
fi

echo ""
echo "Dependencies installed successfully!"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env: cp .env.example .env"
echo "2. Edit .env with your settings: nano .env"
echo "3. Run the setup script: bash setup_ubuntu16.sh"
