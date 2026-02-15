#!/usr/bin/env python3
"""
MySQL Database Backup Script
Backs up MySQL database, compresses it, uploads to Mega, and sends email notification
Requires Python 3.7+
"""

from __future__ import annotations
import os
import subprocess
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import gzip
import shutil
import sys

# Check Python version
if sys.version_info < (3, 7):
    print("Error: This script requires Python 3.7 or higher.")
    print(f"Current version: {sys.version}")
    print("\nPlease upgrade Python:")
    print("  Ubuntu/Debian: sudo apt-get install python3.7 python3.7-venv")
    print("  Or use pyenv to install a newer Python version")
    sys.exit(1)

try:
    from mega import Mega
except ImportError:
    print("Error: mega.py library not installed.")
    print("Please run: pip install mega.py")
    sys.exit(1)

# Configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'mydatabase')

MEGA_EMAIL = os.getenv('MEGA_EMAIL', '')
MEGA_PASSWORD = os.getenv('MEGA_PASSWORD', '')

SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
EMAIL_FROM = os.getenv('EMAIL_FROM', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
EMAIL_TO = os.getenv('EMAIL_TO', '')

BACKUP_DIR = os.getenv('BACKUP_DIR', './backups')


def create_backup_dir():
    """Create backup directory if it doesn't exist"""
    Path(BACKUP_DIR).mkdir(parents=True, exist_ok=True)


def backup_database():
    """Backup MySQL database using mysqldump"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"{BACKUP_DIR}/{DB_NAME}_{timestamp}.sql"
    
    print(f"Creating backup of database '{DB_NAME}'...")
    
    cmd = [
        'mysqldump',
        f'-h{DB_HOST}',
        f'-u{DB_USER}',
        f'-p{DB_PASSWORD}',
        DB_NAME
    ]
    
    try:
        with open(backup_file, 'w') as f:
            subprocess.run(cmd, stdout=f, check=True, stderr=subprocess.PIPE)
        print(f"Backup created: {backup_file}")
        return backup_file
    except subprocess.CalledProcessError as e:
        print(f"Error creating backup: {e.stderr.decode()}")
        raise


def compress_backup(backup_file):
    """Compress backup file using gzip"""
    compressed_file = f"{backup_file}.gz"
    
    print(f"Compressing backup...")
    
    with open(backup_file, 'rb') as f_in:
        with gzip.open(compressed_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    os.remove(backup_file)
    print(f"Compressed backup: {compressed_file}")
    return compressed_file


def upload_to_mega(file_path):
    """Upload file to Mega cloud storage"""
    print(f"Uploading to Mega...")
    
    mega = Mega()
    m = mega.login(MEGA_EMAIL, MEGA_PASSWORD)
    
    file = m.upload(file_path)
    link = m.get_upload_link(file)
    
    print(f"Upload complete!")
    return link


def send_email(backup_link, backup_file):
    """Send email notification with backup link"""
    print(f"Sending email notification...")
    
    subject = f"MySQL Backup - {DB_NAME} - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    body = f"""
    MySQL Database Backup Completed
    
    Database: {DB_NAME}
    Backup File: {os.path.basename(backup_file)}
    Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    
    Download Link (Mega):
    {backup_link}
    
    This is an automated backup notification.
    """
    
    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        print(f"Email sent to {EMAIL_TO}")
    except Exception as e:
        print(f"Error sending email: {e}")
        raise


def main():
    """Main backup process"""
    try:
        print("=" * 50)
        print("MySQL Backup Process Started")
        print("=" * 50)
        
        create_backup_dir()
        backup_file = backup_database()
        compressed_file = compress_backup(backup_file)
        backup_link = upload_to_mega(compressed_file)
        send_email(backup_link, compressed_file)
        
        print("=" * 50)
        print("Backup Process Completed Successfully!")
        print("=" * 50)
        
    except Exception as e:
        print(f"Backup process failed: {e}")
        exit(1)


if __name__ == "__main__":
    main()
