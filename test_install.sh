#!/bin/bash
# Quick test to show the installer is working

echo "Testing installer components..."
echo ""

# Test 1: Check if setup.sh exists
if [ -f setup.sh ]; then
    echo "✓ setup.sh found"
else
    echo "✗ setup.sh NOT FOUND"
    exit 1
fi

# Test 2: Check if it's executable
if [ -x setup.sh ]; then
    echo "✓ setup.sh is executable"
else
    echo "✗ setup.sh is not executable"
    exit 1
fi

# Test 3: Check if install.py exists
if [ -f install.py ]; then
    echo "✓ install.py found"
else
    echo "✗ install.py NOT FOUND"
    exit 1
fi

# Test 4: Check Python
if command -v python3 &> /dev/null; then
    PY_VERSION=$(python3 --version)
    echo "✓ Python found: $PY_VERSION"
else
    echo "✗ Python 3 not found"
    exit 1
fi

# Test 5: Check install.py syntax
if python3 -m py_compile install.py 2>/dev/null; then
    echo "✓ install.py syntax is valid"
else
    echo "✗ install.py has syntax errors"
    exit 1
fi

echo ""
echo "All tests passed! The installer should work."
echo ""
echo "To run the full installation:"
echo "  ./setup.sh"
echo ""
echo "This will:"
echo "  1. Create a virtual environment (1-2 minutes)"
echo "  2. Download and install packages (3-5 minutes)"
echo "  3. Ask for your OpenAI API key (you can press Enter to skip)"
echo "  4. Create the database"
echo "  5. Generate sample data (30 seconds)"
echo ""
echo "Total time: 5-10 minutes depending on internet speed"
