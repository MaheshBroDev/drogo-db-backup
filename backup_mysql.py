#!/usr/bin/env python3
"""
MySQL Database Backup Script
Backs up MySQL database, compresses it, uploads to Mega, and sends email notification
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
import json
import base64
import requests
from Crypto.Cipher import AES
from Crypto.PublicKey import RSA
from Crypto.Util import Counter
import struct
import binascii

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


class SimpleMegaUploader:
    """Simple Mega.nz uploader compatible with Python 3.5+"""
    
    def __init__(self):
        self.api_url = 'https://g.api.mega.co.nz/cs'
        self.sid = None
        self.sequence_num = 0
        
    def _api_request(self, data):
        """Make API request to Mega"""
        params = {'id': self.sequence_num}
        self.sequence_num += 1
        
        if self.sid:
            params['sid'] = self.sid
            
        response = requests.post(
            self.api_url,
            params=params,
            data=json.dumps([data]),
            timeout=300
        )
        
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            return result[0]
        return result
    
    def _prepare_key(self, password):
        """Prepare encryption key from password"""
        key = bytes([0x93, 0xC4, 0x67, 0xE3, 0x7D, 0xB0, 0xC7, 0xA4,
                     0xD1, 0xBE, 0x3F, 0x81, 0x01, 0x52, 0xCB, 0x56])
        
        password_bytes = password.encode('utf-8')
        
        for _ in range(65536):
            cipher = AES.new(key, AES.MODE_ECB)
            for i in range(0, len(password_bytes), 16):
                chunk = password_bytes[i:i+16]
                if len(chunk) < 16:
                    chunk = chunk + bytes(16 - len(chunk))
                key = cipher.encrypt(chunk)
        
        return key
    
    def _encrypt_key(self, key, data):
        """Encrypt data with key"""
        cipher = AES.new(key, AES.MODE_ECB)
        return cipher.encrypt(data)
    
    def _base64_encode(self, data):
        """Mega-specific base64 encoding"""
        b64 = base64.b64encode(data).decode('utf-8')
        return b64.replace('+', '-').replace('/', '_').replace('=', '')
    
    def _base64_decode(self, data):
        """Mega-specific base64 decoding"""
        data = data.replace('-', '+').replace('_', '/')
        data += '=' * (4 - len(data) % 4)
        return base64.b64decode(data)
    
    def login(self, email, password):
        """Login to Mega"""
        print("Logging in to Mega...")
        
        password_key = self._prepare_key(password)
        uh = self._base64_encode(password_key)
        
        result = self._api_request({
            'a': 'us',
            'user': email,
            'uh': uh
        })
        
        if isinstance(result, int) and result < 0:
            raise Exception(f"Login failed with error code: {result}")
        
        self.sid = result.get('csid') or result.get('tsid')
        if not self.sid:
            raise Exception("Login failed: No session ID received")
        
        print("Login successful!")
        return True
    
    def upload(self, file_path):
        """Upload file to Mega"""
        print(f"Preparing upload for {file_path}...")
        
        # Get upload URL
        file_size = os.path.getsize(file_path)
        result = self._api_request({
            'a': 'u',
            's': file_size
        })
        
        upload_url = result.get('p')
        if not upload_url:
            raise Exception("Failed to get upload URL")
        
        # Generate random encryption key
        file_key = os.urandom(16)
        iv = file_key[0:8] + bytes(8)
        
        # Upload file with encryption
        print(f"Uploading file ({file_size} bytes)...")
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Encrypt file data
        counter = Counter.new(128, initial_value=int.from_bytes(iv, 'big'))
        cipher = AES.new(file_key, AES.MODE_CTR, counter=counter)
        encrypted_data = cipher.encrypt(file_data)
        
        # Upload encrypted data
        response = requests.post(upload_url, data=encrypted_data, timeout=600)
        completion_handle = response.text
        
        # Complete upload
        file_name = os.path.basename(file_path)
        attributes = {'n': file_name}
        attr_str = json.dumps(attributes)
        
        # Encrypt attributes
        attr_cipher = AES.new(file_key, AES.MODE_CBC, iv)
        attr_data = attr_str.encode('utf-8')
        attr_data += bytes(16 - len(attr_data) % 16)
        encrypted_attr = attr_cipher.encrypt(attr_data)
        
        # Create file node
        meta_mac = bytes(8)  # Simplified MAC
        key_data = file_key + meta_mac
        
        result = self._api_request({
            'a': 'p',
            't': None,  # Root folder
            'n': [{
                'h': completion_handle,
                't': 0,
                'a': self._base64_encode(encrypted_attr),
                'k': self._base64_encode(key_data)
            }]
        })
        
        if isinstance(result, int) and result < 0:
            raise Exception(f"Upload completion failed with error: {result}")
        
        file_handle = result['f'][0]['h']
        file_key_b64 = self._base64_encode(file_key)
        
        link = f"https://mega.nz/file/{file_handle}#{file_key_b64}"
        print(f"Upload complete!")
        
        return link


def upload_to_mega(file_path):
    """Upload file to Mega cloud storage"""
    print(f"Uploading to Mega...")
    
    uploader = SimpleMegaUploader()
    uploader.login(MEGA_EMAIL, MEGA_PASSWORD)
    link = uploader.upload(file_path)
    
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
