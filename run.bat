@echo off
echo Starting Minecraft Server Manager...
echo.

:: Check if virtual environment exists
if not exist minecraft_server_env (
    echo ERROR: Virtual environment not found
    echo Please run setup.bat first
    pause
    exit /b 1
)

:: Activate virtual environment
call minecraft_server_env\Scripts\activate.bat

:: Check if Java is installed
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Java is not installed or not in PATH
    echo Java is required to run the Minecraft server
    echo Please install Java 17+ from https://adoptium.net/
    echo.
    echo The web interface will still work, but you won't be able to start the Minecraft server.
    echo.
)

:: Start the application
echo Starting the web server...
echo.
echo Access the web interface at: http://localhost:3000
echo Press Ctrl+C to stop the server
echo.
python app.py 