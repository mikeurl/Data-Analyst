#!/bin/bash
# Test script to diagnose why the web page won't open

echo "========================================================================"
echo "DIAGNOSING WEB PAGE LAUNCH ISSUE"
echo "========================================================================"
echo ""

# Test 1: Check if database exists
echo "Test 1: Does the database exist?"
if [ -f "ipeds_data.db" ]; then
    SIZE=$(ls -lh ipeds_data.db | awk '{print $5}')
    echo "✓ Database found: ipeds_data.db ($SIZE)"

    # Check if it has data
    COUNT=$(sqlite3 ipeds_data.db "SELECT COUNT(*) FROM students;" 2>/dev/null)
    if [ $? -eq 0 ]; then
        echo "✓ Database has data: $COUNT students"
    else
        echo "✗ Database exists but might be empty or corrupted"
    fi
else
    echo "✗ Database NOT found!"
    echo "  You need to create it first:"
    echo "  python create_ipeds_db_schema.py"
    echo "  python SyntheticDataforSchema2.py"
fi
echo ""

# Test 2: Check if virtual environment exists
echo "Test 2: Does virtual environment exist?"
if [ -d "venv" ]; then
    echo "✓ Virtual environment found"
else
    echo "✗ Virtual environment NOT found"
    echo "  Run: python3 -m venv venv"
fi
echo ""

# Test 3: Check if packages are installed
echo "Test 3: Are required packages installed?"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate

    MISSING=""
    for PKG in pandas numpy openai gradio; do
        if python -c "import $PKG" 2>/dev/null; then
            echo "✓ $PKG installed"
        else
            echo "✗ $PKG NOT installed"
            MISSING="$MISSING $PKG"
        fi
    done

    if [ -n "$MISSING" ]; then
        echo ""
        echo "Missing packages:$MISSING"
        echo "Install with: pip install -r requirements.txt"
    fi
else
    echo "✗ Can't check - venv not found"
fi
echo ""

# Test 4: Check if API key is configured
echo "Test 4: Is API key configured?"
if [ -f ".env" ]; then
    if grep -q "OPENAI_API_KEY=sk-" .env; then
        echo "✓ API key appears to be configured"
    elif grep -q "OPENAI_API_KEY=.*demo.*" .env 2>/dev/null; then
        echo "⚠ Demo API key found (won't work for real queries)"
    else
        echo "⚠ .env exists but API key may not be set correctly"
    fi
else
    echo "⚠ No .env file found (API features won't work)"
    echo "  The assistant can still start, but won't answer questions"
fi
echo ""

# Test 5: Try to import the AI assistant
echo "Test 5: Can Python import the AI assistant?"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    python -c "import ai_sql_python_assistant" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✓ AI assistant script is valid"
    else
        echo "✗ AI assistant has import errors"
        echo "  Trying to show the error..."
        python -c "import ai_sql_python_assistant" 2>&1 | head -20
    fi
else
    echo "✗ Can't test - venv not found"
fi
echo ""

# Test 6: Check if port 7860 is already in use
echo "Test 6: Is port 7860 available?"
if command -v lsof &> /dev/null; then
    PORT_CHECK=$(lsof -i :7860 2>/dev/null)
    if [ -n "$PORT_CHECK" ]; then
        echo "✗ Port 7860 is already in use!"
        echo "$PORT_CHECK"
        echo ""
        echo "Solution: Kill the process using port 7860, or edit ai_sql_python_assistant.py"
        echo "to use a different port (change server_port=7860 to server_port=7861)"
    else
        echo "✓ Port 7860 is available"
    fi
else
    echo "⚠ Can't check (lsof not available)"
fi
echo ""

echo "========================================================================"
echo "SOLUTION"
echo "========================================================================"
echo ""
echo "To launch the AI assistant, run:"
echo ""
echo "  source venv/bin/activate"
echo "  python ai_sql_python_assistant.py"
echo ""
echo "Then open your browser to: http://localhost:7860"
echo ""
echo "Or use the quick launcher:"
echo "  ./start.sh"
echo ""
