@echo off
REM IPEDS Data Analysis Toolkit - Quick Start Script for Windows
REM This script activates the virtual environment and launches the AI assistant

echo.
echo ========================================================================
echo  IPEDS Data Analysis Toolkit - Starting AI Assistant
echo ========================================================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found
    echo.
    echo Please run setup.bat first to install the toolkit
    echo.
    pause
    exit /b 1
)

REM Check if database exists
if not exist "ipeds_data.db" (
    echo WARNING: Database file not found
    echo.
    echo You need to generate data first. Would you like to generate it now?
    echo This will take about 30 seconds.
    echo.
    choice /C YN /M "Generate sample data"
    if errorlevel 2 goto :skipdata
    if errorlevel 1 goto :gendata

    :gendata
    echo.
    echo Generating sample data...
    call venv\Scripts\activate.bat
    python SyntheticDataforSchema2.py
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to generate data
        pause
        exit /b 1
    )
    goto :launch

    :skipdata
    echo.
    echo Skipping data generation. The AI assistant may not work properly.
    echo Run: python SyntheticDataforSchema2.py to generate data later.
    echo.
    pause
)

:launch
REM Activate virtual environment and launch
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Launching AI Assistant...
echo The web interface will open at http://localhost:7860
echo.
echo Press Ctrl+C to stop the server when you're done
echo.

python ai_sql_python_assistant.py

REM Deactivate on exit
call venv\Scripts\deactivate.bat
