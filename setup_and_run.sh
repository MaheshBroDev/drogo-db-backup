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

# Find suitable Python version (3.5+)
PYTHON_CMD=""
for cmd in python3.11 python3.10 python3.9 python3.8 python3.7 python3.6 python3.5 python3; do
    if command -v $cmd &> /dev/null; then
        VERSION=$($cmd -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        MAJOR=$(echo $VERSION | cut -d. -f1)
        MINOR=$(echo $VERSION | cut -d. -f2)
        
        if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 5 ]; then
            PYTHON_CMD=$cmd
            echo "Found suitable Python: $cmd (version $VERSION)"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "Error: Python 3.5 or higher is required."
    echo "Current Python version is too old."
    echo ""
    if [ "$OS" = "linux" ]; then
        echo "Install Python 3 on Ubuntu/Debian:"
        echo "  sudo apt-get update"
        echo "  sudo apt-get install python3 python3-pip python3-venv"
    elif [ "$OS" = "macos" ]; then
        echo "Install with: brew install python3"
    fi
    exit 1
fi

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
        virtualenv -p $PYTHON_CMD venv
    # Method 2: Try python -m venv
    elif $PYTHON_CMD -m venv venv 2>/dev/null; then
        echo "Using $PYTHON_CMD -m venv..."
    # Method 3: Install virtualenv and try again
    else
        echo "Standard venv not available. Installing virtualenv..."
        
        # Try pip
        if $PYTHON_CMD -m pip --version &> /dev/null; then
            $PYTHON_CMD -m pip install --user virtualenv
            if [ -f "$HOME/.local/bin/virtualenv" ]; then
                $HOME/.local/bin/virtualenv -p $PYTHON_CMD venv
            elif command -v virtualenv &> /dev/null; then
                virtualenv -p $PYTHON_CMD venv
            fi
        else
            echo "Error: pip not found. Please install pip:"
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
            echo "  $PYTHON_CMD -m pip install --user virtualenv"
            echo "  ~/.local/bin/virtualenv -p $PYTHON_CMD venv"
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

# Check if rclone is available
if ! command -v rclone &> /dev/null; then
    echo "Warning: rclone not found. Please install rclone."
    echo "  Install: curl https://rclone.org/install.sh | sudo bash"
    echo "  Or visit: https://rclone.org/downloads/"
    deactivate
    exit 1
fi

echo "rclone found: $(rclone version | head -n 1)"

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
