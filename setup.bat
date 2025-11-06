@echo off
REM IPEDS Data Analysis Toolkit - Windows Installer
REM This script automatically sets up the entire toolkit

echo.
echo ========================================================================
echo  IPEDS Data Analysis Toolkit - Windows Quick Installer
echo ========================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo Please install Python 3.8 or higher from:
    echo https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

echo Python found. Starting installation...
echo.

REM Run the Python installer
python install.py %*

if errorlevel 1 (
    echo.
    echo Installation encountered errors. Please review the output above.
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================================================
echo  Installation Complete!
echo ========================================================================
echo.
echo To launch the AI Assistant, run: start.bat
echo Or open a new Command Prompt and run:
echo   venv\Scripts\activate
echo   python ai_sql_python_assistant.py
echo.

pause
