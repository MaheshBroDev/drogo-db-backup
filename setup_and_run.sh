#!/bin/bash

# Universal MySQL Backup Script Setup and Run
# Works on: Ubuntu 14.04+, Debian, macOS, WSL

echo "=========================================="
echo "MySQL Backup Setup and Execution"
echo "=========================================="

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
fi

echo "Detected OS: $OS"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed."
    if [ "$OS" = "linux" ]; then
        echo "Install with: sudo apt-get install python3 python3-pip"
    elif [ "$OS" = "macos" ]; then
        echo "Install with: brew install python3"
    fi
    exit 1
fi

echo "Python 3 found: $(python3 --version)"

# Remove incomplete venv if exists
if [ -d "venv" ] && [ ! -f "venv/bin/activate" ]; then
    echo "Removing incomplete virtual environment..."
    rm -rf venv
fi

# Create virtual environment with multiple fallback methods
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    
    # Method 1: Try virtualenv (most reliable for older systems)
    if command -v virtualenv &> /dev/null; then
        echo "Using virtualenv..."
        virtualenv -p python3 venv
    # Method 2: Try python3 -m venv
    elif python3 -m venv venv 2>/dev/null; then
        echo "Using python3 -m venv..."
    # Method 3: Install virtualenv and try again
    else
        echo "Standard venv not available. Installing virtualenv..."
        
        # Try pip3
        if command -v pip3 &> /dev/null; then
            pip3 install --user virtualenv
            if [ -f "$HOME/.local/bin/virtualenv" ]; then
                $HOME/.local/bin/virtualenv -p python3 venv
            elif command -v virtualenv &> /dev/null; then
                virtualenv -p python3 venv
            fi
        else
            echo "Error: pip3 not found. Please install python3-pip:"
            if [ "$OS" = "linux" ]; then
                echo "  sudo apt-get install python3-pip python3-venv"
            fi
            exit 1
        fi
    fi
    
    # Verify venv was created successfully
    if [ ! -f "venv/bin/activate" ]; then
        echo ""
        echo "Error: Failed to create virtual environment."
        echo ""
        if [ "$OS" = "linux" ]; then
            echo "Please install required packages:"
            echo "  sudo apt-get update"
            echo "  sudo apt-get install python3 python3-pip python3-venv"
            echo ""
            echo "Or install virtualenv manually:"
            echo "  pip3 install --user virtualenv"
            echo "  ~/.local/bin/virtualenv -p python3 venv"
        fi
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
