@echo off
REM MySQL Backup Script Setup and Run (Windows)

echo ==========================================
echo MySQL Backup Setup and Execution
echo ==========================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3 from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python found:
python --version

REM Check if venv exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
) else (
    echo Virtual environment already exists.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing dependencies...
pip install -r requirements.txt

if errorlevel 1 (
    echo Error: Failed to install dependencies.
    call venv\Scripts\deactivate.bat
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo.
    echo Warning: .env file not found!
    echo Please copy .env.example to .env and configure your settings:
    echo   copy .env.example .env
    echo   notepad .env
    echo.
    call venv\Scripts\deactivate.bat
    pause
    exit /b 1
)

REM Check if mysqldump is available
where mysqldump >nul 2>&1
if errorlevel 1 (
    echo Warning: mysqldump not found in PATH.
    echo Please install MySQL and add it to your PATH, or specify the full path.
    echo Download from: https://dev.mysql.com/downloads/mysql/
    call venv\Scripts\deactivate.bat
    pause
    exit /b 1
)

REM Run backup script
echo.
echo Starting backup process...
echo.
python backup_mysql.py

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat

echo.
echo Script execution completed.
pause
