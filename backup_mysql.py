#!/usr/bin/env python3
"""
MySQL Database Backup Script
Backs up MySQL database, compresses it, uploads to cloud storage via rclone, and sends email notification
Compatible with Python 3.5+
"""

import os
import subprocess
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import gzip
import shutil
import sys

# Configuration
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'mydatabase')

# Rclone configuration
RCLONE_REMOTE = os.getenv('RCLONE_REMOTE', 'mega:backups')  # e.g., 'mega:backups' or 'gdrive:backups'

# Email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))
EMAIL_FROM = os.getenv('EMAIL_FROM', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
EMAIL_TO = os.getenv('EMAIL_TO', '')

BACKUP_DIR = os.getenv('BACKUP_DIR', './backups')


def create_backup_dir():
    """Create backup directory if it doesn't exist"""
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)


def backup_database():
    """Backup MySQL database using mysqldump"""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = "{}/{}_{}.sql".format(BACKUP_DIR, DB_NAME, timestamp)
    
    print("Creating backup of database '{}'...".format(DB_NAME))
    
    cmd = [
        'mysqldump',
        '-h{}'.format(DB_HOST),
        '-u{}'.format(DB_USER),
        '-p{}'.format(DB_PASSWORD),
        DB_NAME
    ]
    
    try:
        with open(backup_file, 'w') as f:
            subprocess.run(cmd, stdout=f, check=True, stderr=subprocess.PIPE)
        print("Backup created: {}".format(backup_file))
        return backup_file
    except subprocess.CalledProcessError as e:
        print("Error creating backup: {}".format(e.stderr.decode()))
        raise


def compress_backup(backup_file):
    """Compress backup file using gzip"""
    compressed_file = "{}.gz".format(backup_file)
    
    print("Compressing backup...")
    
    with open(backup_file, 'rb') as f_in:
        with gzip.open(compressed_file, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    os.remove(backup_file)
    print("Compressed backup: {}".format(compressed_file))
    return compressed_file


def check_rclone():
    """Check if rclone is installed"""
    try:
        subprocess.run(['rclone', 'version'], 
                      stdout=subprocess.PIPE, 
                      stderr=subprocess.PIPE, 
                      check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def upload_to_cloud(file_path):
    """Upload file to cloud storage using rclone"""
    print("Uploading to cloud storage via rclone...")
    
    if not check_rclone():
        raise Exception("rclone is not installed. Please install rclone first.")
    
    file_name = os.path.basename(file_path)
    remote_path = "{}/{}".format(RCLONE_REMOTE, file_name)
    
    print("Uploading {} to {}...".format(file_name, RCLONE_REMOTE))
    
    cmd = ['rclone', 'copy', file_path, RCLONE_REMOTE, '-P']
    
    try:
        result = subprocess.run(cmd, check=True, stderr=subprocess.PIPE)
        print("Upload complete!")
        
        # Generate link (for supported remotes)
        link_cmd = ['rclone', 'link', remote_path]
        try:
            link_result = subprocess.run(
                link_cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                check=True
            )
            link = link_result.stdout.decode('utf-8').strip()
            return link
        except subprocess.CalledProcessError:
            # If link generation fails, return the remote path
            return "File uploaded to: {}".format(remote_path)
            
    except subprocess.CalledProcessError as e:
        error_msg = e.stderr.decode('utf-8') if e.stderr else str(e)
        raise Exception("Upload failed: {}".format(error_msg))


def send_email(backup_link, backup_file):
    """Send email notification with backup link"""
    print("Sending email notification...")
    
    subject = "MySQL Backup - {} - {}".format(
        DB_NAME,
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    )
    
    body = """
    MySQL Database Backup Completed
    
    Database: {}
    Backup File: {}
    Timestamp: {}
    
    Cloud Storage Location:
    {}
    
    This is an automated backup notification.
    """.format(
        DB_NAME,
        os.path.basename(backup_file),
        datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        backup_link
    )
    
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
        print("Email sent to {}".format(EMAIL_TO))
    except Exception as e:
        print("Error sending email: {}".format(e))
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
        backup_link = upload_to_cloud(compressed_file)
        send_email(backup_link, compressed_file)
        
        print("=" * 50)
        print("Backup Process Completed Successfully!")
        print("=" * 50)
        
    except Exception as e:
        print("Backup process failed: {}".format(e))
        exit(1)


if __name__ == "__main__":
    main()
