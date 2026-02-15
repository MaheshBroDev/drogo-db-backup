# MySQL Database Backup to Cloud Storage

Automated MySQL database backup script that compresses the backup, uploads it to cloud storage via rclone, and sends an email notification with the location.

**Optimized for Mega.nz storage** - See [MEGA_SETUP.md](MEGA_SETUP.md) for detailed Mega configuration guide.

## Features

- MySQL database backup using mysqldump
- Gzip compression to reduce file size
- Upload to any cloud storage supported by rclone (70+ providers)
- Email notification with file location/link
- Virtual environment support
- Cross-platform (Windows, Linux, macOS)
- Supports: Mega, Google Drive, Dropbox, S3, OneDrive, and many more

## Prerequisites

- Python 3.5 or higher
- MySQL client tools (mysqldump)
- rclone installed and configured
- Cloud storage account (Mega, Google Drive, Dropbox, S3, etc.)
- Email account (Gmail recommended with app password)

## Installation

### Linux/macOS (All versions including Ubuntu 16.04+, Debian, CentOS)

1. Install rclone:
   ```bash
   curl https://rclone.org/install.sh | sudo bash
   ```

2. Configure rclone with your cloud storage:
   ```bash
   rclone config
   ```
   Follow the prompts to set up your remote (e.g., "mega", "gdrive", "dropbox")

3. Clone or download this project

4. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

5. Edit `.env` with your configuration:
   ```bash
   nano .env
   ```
   Set `RCLONE_REMOTE` to your configured remote (e.g., `mega:backups`)

6. Make the script executable:
   ```bash
   chmod +x setup_and_run.sh
   ```

7. Run the setup and backup:
   ```bash
   bash setup_and_run.sh
   ```

**Note:** Works with Python 3.5+ (Ubuntu 16.04 default Python 3.5.2 is supported)

### Windows

1. Install rclone:
   - Download from https://rclone.org/downloads/
   - Extract and add to PATH, or use: `choco install rclone`

2. Configure rclone with your cloud storage:
   ```cmd
   rclone config
   ```
   Follow the prompts to set up your remote

3. Clone or download this project

4. Copy the example environment file:
   ```cmd
   copy .env.example .env
   ```

5. Edit `.env` with your configuration:
   ```cmd
   notepad .env
   ```
   Set `RCLONE_REMOTE` to your configured remote (e.g., `mega:backups`)

6. Run the setup and backup:
   ```cmd
   setup_and_run.cmd
   ```

## Configuration

Edit the `.env` file with your settings:

### MySQL Configuration
- `DB_HOST`: MySQL server host (default: localhost)
- `DB_USER`: MySQL username
- `DB_PASSWORD`: MySQL password
- `DB_NAME`: Database name to backup

### Rclone Configuration
- `RCLONE_REMOTE`: Your rclone remote and path (e.g., `mega:backups`, `gdrive:backups`)
  - Run `rclone config` to set up remotes
  - Run `rclone listremotes` to see configured remotes

### Email Configuration
- `SMTP_SERVER`: SMTP server (default: smtp.gmail.com)
- `SMTP_PORT`: SMTP port (default: 587)
- `EMAIL_FROM`: Sender email address
- `EMAIL_PASSWORD`: Email password (use app password for Gmail)
- `EMAIL_TO`: Recipient email address

### Rclone Setup Examples

Configure rclone for different providers:

```bash
# Mega.nz
rclone config
# Choose: n (new remote)
# Name: mega
# Storage: mega
# Enter your Mega email and password

# Google Drive
rclone config
# Choose: n (new remote)
# Name: gdrive
# Storage: drive
# Follow OAuth flow

# Dropbox
rclone config
# Choose: n (new remote)
# Name: dropbox
# Storage: dropbox
# Follow OAuth flow
```

### Gmail App Password

For Gmail, you need to use an App Password:
1. Enable 2-Factor Authentication on your Google account
2. Go to https://myaccount.google.com/apppasswords
3. Generate a new app password
4. Use this password in `EMAIL_PASSWORD`

## Manual Usage

If you want to run the script manually after initial setup:

```bash
# Linux/macOS
source venv/bin/activate
python backup_mysql.py
deactivate

# Windows
venv\Scripts\activate.bat
python backup_mysql.py
deactivate
```

## Scheduling Backups

### Linux/macOS (cron)

Add to crontab (`crontab -e`):
```bash
# Daily backup at 2 AM
0 2 * * * cd /path/to/backup/script && bash setup_and_run.sh >> backup.log 2>&1
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily, weekly, etc.)
4. Action: Start a program
5. Program: `cmd.exe`
6. Arguments: `/c "cd /d C:\path\to\backup\script && setup_and_run.cmd"`

## Troubleshooting

### Virtual environment issues
If you see "venv/bin/activate not found" or venv creation fails:
```bash
# Remove incomplete venv
rm -rf venv

# Install required packages (Ubuntu 16.04+)
sudo apt-get update
sudo apt-get install python3 python3-pip python3-venv

# The script will automatically detect Python 3.5+
bash setup_and_run.sh
```

### rclone not found
- **Ubuntu/Debian**: `curl https://rclone.org/install.sh | sudo bash`
- **macOS**: `brew install rclone`
- **Windows**: Download from https://rclone.org/downloads/

### mysqldump not found
- **Ubuntu/Debian**: `sudo apt-get install mysql-client`
- **CentOS/RHEL**: `sudo yum install mysql`
- **macOS**: `brew install mysql-client`
- **Windows**: Install MySQL and add to PATH

### Upload fails
- Check rclone configuration: `rclone config`
- Test connection: `rclone lsd remote_name:`
- Verify remote path exists
- Check cloud storage quota

### Email sending fails
- Verify SMTP settings
- For Gmail, use an app password
- Check firewall settings

## Security Notes

- Never commit `.env` file to version control
- Use app passwords instead of main passwords
- Restrict file permissions on `.env`: `chmod 600 .env`
- Consider encrypting backups for sensitive data

## License

MIT License
