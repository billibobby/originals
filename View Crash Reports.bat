@echo off
echo.
echo ==========================================
echo   The Originals - Crash Report Viewer
echo ==========================================
echo.

if not exist "logs\crashes" (
    echo No crash reports found.
    pause
    exit /b 0
)

echo Recent crash reports:
echo.
dir /b /o:-d "logs\crashes\*.json" | head -10

echo.
set /p "report=Enter crash report filename to view (or press Enter to exit): "

if "%report%"=="" exit /b 0

if exist "logs\crashes\%report%" (
    type "logs\crashes\%report%"
) else (
    echo Crash report not found: %report%
)

echo.
pause
