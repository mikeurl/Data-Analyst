@echo off
REM Fix everything and launch the AI assistant - Windows version

echo ========================================================================
echo FIX ^& LAUNCH - Get the AI Assistant running in 5 minutes
echo ========================================================================
echo.

REM Step 1: Create virtual environment if needed
echo Step 1: Setting up virtual environment...
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)
call venv\Scripts\activate.bat
echo [92m✓ Virtual environment activated[0m
echo.

REM Step 2: Install packages
echo Step 2: Installing packages...
echo This will take 2-3 minutes. Please wait...
echo.
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
echo [92m✓ Packages installed[0m
echo.

REM Step 3: Create .env file if it doesn't exist
echo Step 3: Configuring API key...
if not exist ".env" (
    echo Creating .env file with placeholder...
    (
        echo # OpenAI API Configuration
        echo # Replace this with your actual API key from https://platform.openai.com/api-keys
        echo OPENAI_API_KEY=sk-placeholder-replace-with-real-key
    ) > .env
    echo [93m⚠ Using placeholder API key[0m
    echo   To use AI features, edit .env and add your real OpenAI API key
) else (
    echo [92m✓ .env file exists[0m
)
echo.

REM Step 4: Create database
echo Step 4: Creating database...
if not exist "ipeds_data.db" (
    echo Creating database schema...
    python create_ipeds_db_schema.py
    echo.
    echo Generating sample data (this takes ~30 seconds^)...
    python SyntheticDataforSchema2.py
    echo [92m✓ Database created with sample data[0m
) else (
    echo [92m✓ Database already exists[0m
)
echo.

REM Step 5: Launch the AI assistant
echo ========================================================================
echo LAUNCHING AI ASSISTANT
echo ========================================================================
echo.
echo Starting web server on http://localhost:7860
echo.
echo [93m⚠ IMPORTANT:[0m
echo   1. The web page should open automatically
echo   2. If not, manually open: http://localhost:7860
echo   3. Press Ctrl+C when you want to stop the server
echo.
echo Note: The placeholder API key won't work. To use AI features:
echo   1. Stop the server (Ctrl+C^)
echo   2. Edit .env file and add your real OpenAI API key
echo   3. Run this script again
echo.
echo Starting in 3 seconds...
timeout /t 3 /nobreak >nul
echo.

python ai_sql_python_assistant.py

REM Deactivate on exit
call venv\Scripts\deactivate.bat
