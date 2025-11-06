#!/bin/bash
# IPEDS Data Analysis Toolkit - Mac/Linux Installer
# This script automatically sets up the entire toolkit

echo ""
echo "========================================================================"
echo " IPEDS Data Analysis Toolkit - Mac/Linux Quick Installer"
echo "========================================================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo ""
    echo "Please install Python 3.8 or higher:"
    echo ""
    echo "  macOS:  brew install python3"
    echo "  Ubuntu: sudo apt install python3 python3-pip python3-venv"
    echo "  Fedora: sudo dnf install python3 python3-pip"
    echo ""
    exit 1
fi

echo "Python found. Starting installation..."
echo ""

# Run the Python installer
python3 install.py "$@"

if [ $? -ne 0 ]; then
    echo ""
    echo "Installation encountered errors. Please review the output above."
    echo ""
    exit 1
fi

echo ""
echo "========================================================================"
echo " Installation Complete!"
echo "========================================================================"
echo ""
echo "To launch the AI Assistant, run: ./start.sh"
echo "Or open a new terminal and run:"
echo "  source venv/bin/activate"
echo "  python ai_sql_python_assistant.py"
echo ""
