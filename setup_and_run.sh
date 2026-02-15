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
    
    # Try virtualenv first (more reliable on older systems)
    if command -v virtualenv &> /dev/null; then
        virtualenv -p python3 venv
    else
        # Try python3 -m venv
        python3 -m venv venv
        
        # If venv creation failed or activate script missing, try installing python3-venv
        if [ ! -f "venv/bin/activate" ]; then
            echo "venv module not fully installed. Attempting to install python3-venv..."
            echo "You may need to run: sudo apt-get install python3-venv python3-pip"
            
            # Try with virtualenv as fallback
            if command -v pip3 &> /dev/null; then
                echo "Installing virtualenv..."
                pip3 install --user virtualenv
                ~/.local/bin/virtualenv -p python3 venv
            fi
        fi
    fi
    
    if [ ! -f "venv/bin/activate" ]; then
        echo "Error: Failed to create virtual environment with activate script."
        echo "Please install python3-venv or virtualenv:"
        echo "  sudo apt-get update"
        echo "  sudo apt-get install python3-venv python3-pip"
        echo "Or install virtualenv:"
        echo "  pip3 install --user virtualenv"
        exit 1
    fi
    echo "Virtual environment created successfully."
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "Error: venv/bin/activate not found."
    echo "Please delete the venv folder and run this script again."
    exit 1
fi

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
