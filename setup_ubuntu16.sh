#!/bin/bash

# MySQL Backup Script Setup for Ubuntu 16.04
# This script handles the older Python environment on Ubuntu 16.04

echo "=========================================="
echo "MySQL Backup Setup (Ubuntu 16.04)"
echo "=========================================="

# Check if running as root for package installation
if [ "$EUID" -eq 0 ]; then 
    CAN_INSTALL=true
else
    CAN_INSTALL=false
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    if [ "$CAN_INSTALL" = true ]; then
        echo "Installing Python 3..."
        apt-get update
        apt-get install -y python3 python3-pip
    else
        echo "Please run: sudo apt-get install python3 python3-pip"
        exit 1
    fi
fi

echo "Python 3 found: $(python3 --version)"

# Install python3-venv if not available
if ! python3 -c "import venv" &> /dev/null; then
    echo "python3-venv not found. Installing..."
    if [ "$CAN_INSTALL" = true ]; then
        apt-get install -y python3-venv
    else
        echo "Please run: sudo apt-get install python3-venv"
        exit 1
    fi
fi

# Remove incomplete venv if exists
if [ -d "venv" ] && [ ! -f "venv/bin/activate" ]; then
    echo "Removing incomplete virtual environment..."
    rm -rf venv
fi

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    
    if [ ! -f "venv/bin/activate" ]; then
        echo "Error: venv creation failed. Trying alternative method..."
        
        # Install virtualenv as fallback
        pip3 install --user virtualenv
        ~/.local/bin/virtualenv -p python3 venv
        
        if [ ! -f "venv/bin/activate" ]; then
            echo "Error: Could not create virtual environment."
            exit 1
        fi
    fi
    echo "Virtual environment created successfully."
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install dependencies."
    deactivate
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo ""
    echo "Warning: .env file not found!"
    echo "Please copy .env.example to .env and configure your settings:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    echo ""
    deactivate
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if mysqldump is available
if ! command -v mysqldump &> /dev/null; then
    echo "Warning: mysqldump not found."
    if [ "$CAN_INSTALL" = true ]; then
        echo "Installing MySQL client..."
        apt-get install -y mysql-client
    else
        echo "Please run: sudo apt-get install mysql-client"
        deactivate
        exit 1
    fi
fi

# Run backup script
echo ""
echo "Starting backup process..."
echo ""
python backup_mysql.py

# Deactivate virtual environment
deactivate

echo ""
echo "Script execution completed."
