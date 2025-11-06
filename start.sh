#!/bin/bash
# IPEDS Data Analysis Toolkit - Quick Start Script for Mac/Linux
# This script activates the virtual environment and launches the AI assistant

echo ""
echo "========================================================================"
echo " IPEDS Data Analysis Toolkit - Starting AI Assistant"
echo "========================================================================"
echo ""

# Check if virtual environment exists
if [ ! -f "venv/bin/activate" ]; then
    echo "ERROR: Virtual environment not found"
    echo ""
    echo "Please run ./setup.sh first to install the toolkit"
    echo ""
    exit 1
fi

# Check if database exists
if [ ! -f "ipeds_data.db" ]; then
    echo "WARNING: Database file not found"
    echo ""
    echo "You need to generate data first. Would you like to generate it now?"
    echo "This will take about 30 seconds."
    echo ""
    read -p "Generate sample data? (y/N): " -n 1 -r
    echo ""

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Generating sample data..."
        source venv/bin/activate
        python SyntheticDataforSchema2.py
        if [ $? -ne 0 ]; then
            echo ""
            echo "ERROR: Failed to generate data"
            exit 1
        fi
    else
        echo ""
        echo "Skipping data generation. The AI assistant may not work properly."
        echo "Run: python SyntheticDataforSchema2.py to generate data later."
        echo ""
        read -p "Press Enter to continue..."
    fi
fi

# Activate virtual environment and launch
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Launching AI Assistant..."
echo "The web interface will open at http://localhost:7860"
echo ""
echo "Press Ctrl+C to stop the server when you're done"
echo ""

python ai_sql_python_assistant.py

# Deactivate on exit
deactivate
