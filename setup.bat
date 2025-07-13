@echo off
echo Setting up Minecraft Server Manager...
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

:: Create virtual environment
echo Creating virtual environment...
python -m venv minecraft_server_env
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

:: Activate virtual environment
echo Activating virtual environment...
call minecraft_server_env\Scripts\activate.bat

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install dependencies
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

:: Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file...
    echo SECRET_KEY=your-secret-key-here > .env
    echo MINECRAFT_VERSION=1.20.1 >> .env
    echo SERVER_PORT=3000 >> .env
)

echo.
echo Setup complete!
echo.
echo To start the server, run: run.bat
echo Or manually:
echo   1. minecraft_server_env\Scripts\activate.bat
echo   2. python app.py
echo.
pause 