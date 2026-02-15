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
from Crypto.Util import Counter
import struct

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
            raise Exception("Login failed with error code: {}".format(result))
        
        self.sid = result.get('csid') or result.get('tsid')
        if not self.sid:
            raise Exception("Login failed: No session ID received")
        
        print("Login successful!")
        return True
    
    def upload(self, file_path):
        """Upload file to Mega"""
        print("Preparing upload for {}...".format(file_path))
        
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
        print("Uploading file ({} bytes)...".format(file_size))
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
        
        # Encrypt file data - convert IV to integer for Counter
        iv_int = struct.unpack('>QQ', iv)[0] << 64 | struct.unpack('>QQ', iv)[1]
        counter = Counter.new(128, initial_value=iv_int)
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
            raise Exception("Upload completion failed with error: {}".format(result))
        
        file_handle = result['f'][0]['h']
        file_key_b64 = self._base64_encode(file_key)
        
        link = "https://mega.nz/file/{}#{}".format(file_handle, file_key_b64)
        print("Upload complete!")
        
        return link


def upload_to_mega(file_path):
    """Upload file to Mega cloud storage"""
    print("Uploading to Mega...")
    
    uploader = SimpleMegaUploader()
    uploader.login(MEGA_EMAIL, MEGA_PASSWORD)
    link = uploader.upload(file_path)
    
    return link


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
    
    Download Link (Mega):
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
        backup_link = upload_to_mega(compressed_file)
        send_email(backup_link, compressed_file)
        
        print("=" * 50)
        print("Backup Process Completed Successfully!")
        print("=" * 50)
        
    except Exception as e:
        print("Backup process failed: {}".format(e))
        exit(1)


if __name__ == "__main__":
    main()
