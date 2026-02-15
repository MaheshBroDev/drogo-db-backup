@echo off
REM Universal MySQL Backup Script Setup and Run (Windows)

echo ==========================================
echo MySQL Backup Setup and Execution
echo ==========================================

REM Check if Python is installed (try python3 first, then python)
python3 --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python3
    goto :python_found
)

python --version >nul 2>&1
if not errorlevel 1 (
    set PYTHON_CMD=python
    goto :python_found
)

echo Error: Python is not installed or not in PATH.
echo Please install Python 3 from https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation.
pause
exit /b 1

:python_found
echo Python found:
%PYTHON_CMD% --version

REM Remove incomplete venv if exists
if exist "venv" (
    if not exist "venv\Scripts\activate.bat" (
        echo Removing incomplete virtual environment...
        rmdir /s /q venv
    )
)

REM Create virtual environment
if not exist "venv" (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv venv
    
    if errorlevel 1 (
        echo Error: Failed to create virtual environment.
        echo.
        echo Trying alternative method with virtualenv...
        %PYTHON_CMD% -m pip install --user virtualenv
        %PYTHON_CMD% -m virtualenv venv
        
        if errorlevel 1 (
            echo Error: Could not create virtual environment.
            echo Please ensure Python is properly installed.
            pause
            exit /b 1
        )
    )
    
    if not exist "venv\Scripts\activate.bat" (
        echo Error: Virtual environment created but activate.bat is missing.
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

if errorlevel 1 (
    echo Error: Failed to activate virtual environment.
    pause
    exit /b 1
)

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

REM Check if rclone is available
where rclone >nul 2>&1
if errorlevel 1 (
    echo Warning: rclone not found in PATH.
    echo Please install rclone from: https://rclone.org/downloads/
    echo Or use: choco install rclone
    call venv\Scripts\deactivate.bat
    pause
    exit /b 1
)

echo rclone found:
rclone version

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
