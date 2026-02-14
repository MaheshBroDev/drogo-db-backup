#!/bin/bash

# MySQL Backup Script Setup and Run (Linux/Mac)

echo "=========================================="
echo "MySQL Backup Setup and Execution"
echo "=========================================="

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

echo "Python 3 found: $(python3 --version)"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment."
        exit 1
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
    echo "  nano .env  # or use your preferred editor"
    echo ""
    deactivate
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Check if mysqldump is available
if ! command -v mysqldump &> /dev/null; then
    echo "Warning: mysqldump not found. Please install MySQL client tools."
    echo "  Ubuntu/Debian: sudo apt-get install mysql-client"
    echo "  CentOS/RHEL: sudo yum install mysql"
    echo "  macOS: brew install mysql-client"
    deactivate
    exit 1
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
