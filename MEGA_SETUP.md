# Mega.nz Setup Guide with Rclone

Quick guide to configure rclone with Mega.nz for automated MySQL backups.

## Step 1: Install Rclone

### Ubuntu 16.04 / Linux
```bash
curl https://rclone.org/install.sh | sudo bash
```

### Verify Installation
```bash
rclone version
```

## Step 2: Configure Rclone for Mega

Run the configuration wizard:
```bash
rclone config
```

Follow these steps:

1. **New remote**: Type `n` and press Enter
2. **Name**: Type `mega` (or any name you prefer) and press Enter
3. **Storage**: Type `mega` or find the number for Mega and press Enter
4. **User**: Enter your Mega email address
5. **Password**: 
   - Option 1: Type `y` to enter password
   - Option 2: Type `n` to leave blank (less secure)
6. **Enter password**: Type your Mega password
7. **Confirm**: Type `y` to confirm the configuration
8. **Quit**: Type `q` to quit

## Step 3: Test Your Configuration

List your Mega storage:
```bash
rclone lsd mega:
```

Create a backup folder (optional):
```bash
rclone mkdir mega:backups
```

Test upload:
```bash
echo "test" > test.txt
rclone copy test.txt mega:backups
rclone ls mega:backups
rm test.txt
```

## Step 4: Configure the Backup Script

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit the configuration:
```bash
nano .env
```

3. Set your Mega remote:
```bash
# For root of Mega storage
RCLONE_REMOTE=mega:

# For a specific folder (recommended)
RCLONE_REMOTE=mega:backups

# For nested folders
RCLONE_REMOTE=mega:backups/mysql
```

4. Configure your MySQL and email settings in the same `.env` file

## Step 5: Run the Backup

```bash
bash setup_and_run.sh
```

## Useful Rclone Commands for Mega

### List remotes
```bash
rclone listremotes
```

### List files in Mega
```bash
rclone ls mega:backups
```

### Check Mega storage quota
```bash
rclone about mega:
```

### Generate shareable link (if supported)
```bash
rclone link mega:backups/filename.sql.gz
```

### Delete old backups
```bash
rclone delete mega:backups --min-age 30d
```

### Sync local to Mega
```bash
rclone sync ./backups mega:backups
```

## Troubleshooting

### "Failed to create file system" error
- Check your Mega credentials: `rclone config reconnect mega:`
- Verify your email and password are correct

### "Quota exceeded" error
- Check your storage: `rclone about mega:`
- Delete old backups or upgrade your Mega account

### "Too many requests" error
- Mega has rate limits for free accounts
- Wait a few minutes and try again
- Consider upgrading to Mega Pro

### Connection timeout
- Check your internet connection
- Try increasing timeout: `rclone copy --timeout 10m`

## Mega Storage Limits

### Free Account
- 20 GB storage (with achievements up to 50 GB)
- Transfer quota limits
- Rate limiting on API calls

### Pro Accounts
- Pro Lite: 400 GB storage, 1 TB transfer
- Pro I: 2 TB storage, 2 TB transfer
- Pro II: 8 TB storage, 8 TB transfer
- Pro III: 16 TB storage, 16 TB transfer

## Security Notes

1. **Encryption**: Rclone stores your Mega password encrypted in the config file
2. **Config location**: `~/.config/rclone/rclone.conf`
3. **Protect config**: `chmod 600 ~/.config/rclone/rclone.conf`
4. **Two-factor auth**: Mega 2FA is supported by rclone

## Automated Backups with Cron

Add to crontab (`crontab -e`):

```bash
# Daily backup at 2 AM
0 2 * * * cd /path/to/backup/script && bash setup_and_run.sh >> backup.log 2>&1

# Weekly backup on Sunday at 3 AM
0 3 * * 0 cd /path/to/backup/script && bash setup_and_run.sh >> backup.log 2>&1

# Cleanup old backups (keep last 30 days)
0 4 * * * rclone delete mega:backups --min-age 30d
```

## Getting Shareable Links

The script automatically tries to generate shareable links. If it doesn't work:

```bash
# Manual link generation
rclone link mega:backups/your_backup_file.sql.gz
```

Note: Mega link generation via rclone may have limitations. The script will fall back to showing the file path if link generation fails.
