#!/bin/bash
# Fix everything and launch the AI assistant

echo "========================================================================"
echo "FIX & LAUNCH - Get the AI Assistant running in 5 minutes"
echo "========================================================================"
echo ""

# Step 1: Activate virtual environment
echo "Step 1: Activating virtual environment..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Step 2: Install packages
echo "Step 2: Installing packages..."
echo "This will take 2-3 minutes. Please wait..."
echo ""
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "✓ Packages installed"
echo ""

# Step 3: Create .env file if it doesn't exist
echo "Step 3: Configuring API key..."
if [ ! -f ".env" ]; then
    echo "Creating .env file with placeholder..."
    cat > .env << 'EOF'
# OpenAI API Configuration
# Replace this with your actual API key from https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-placeholder-replace-with-real-key
EOF
    echo "⚠ Using placeholder API key"
    echo "  To use AI features, edit .env and add your real OpenAI API key"
else
    echo "✓ .env file exists"
fi
echo ""

# Step 4: Create database
echo "Step 4: Creating database..."
if [ ! -f "ipeds_data.db" ]; then
    echo "Creating database schema..."
    python create_ipeds_db_schema.py
    echo ""
    echo "Generating sample data (this takes ~30 seconds)..."
    python SyntheticDataforSchema2.py
    echo "✓ Database created with sample data"
else
    echo "✓ Database already exists"
fi
echo ""

# Step 5: Launch the AI assistant
echo "========================================================================"
echo "LAUNCHING AI ASSISTANT"
echo "========================================================================"
echo ""
echo "Starting web server on http://localhost:7860"
echo ""
echo "⚠ IMPORTANT:"
echo "  1. The web page should open automatically"
echo "  2. If not, manually open: http://localhost:7860"
echo "  3. Press Ctrl+C when you want to stop the server"
echo ""
echo "Note: The placeholder API key won't work. To use AI features:"
echo "  1. Stop the server (Ctrl+C)"
echo "  2. Edit .env file and add your real OpenAI API key"
echo "  3. Run this script again"
echo ""
echo "Starting in 3 seconds..."
sleep 3
echo ""

python ai_sql_python_assistant.py
