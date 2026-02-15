#!/bin/bash

# Simple script to run backup after initial setup
# Use this for cron jobs or manual runs after setup is complete

cd "$(dirname "$0")"

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run setup_ubuntu16.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Error: .env file not found."
    deactivate
    exit 1
fi

# Run backup
python backup_mysql.py

# Deactivate
deactivate
