#!/bin/bash

echo "====================================="
echo "Job Shop Scheduler - Setup Script"
echo "====================================="
echo ""

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "✓ Python 3 found"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Check for MiniZinc installation
echo ""
echo "Checking for MiniZinc installation..."
MINIZINC_PATH=""

# Try to find minizinc in PATH
if command -v minizinc &> /dev/null; then
    MINIZINC_PATH=$(which minizinc)
    echo "✓ MiniZinc found in PATH: $MINIZINC_PATH"
# Try common installation locations
elif [ -f "/usr/local/bin/minizinc" ]; then
    MINIZINC_PATH="/usr/local/bin/minizinc"
    echo "✓ MiniZinc found: $MINIZINC_PATH"
elif [ -f "/usr/bin/minizinc" ]; then
    MINIZINC_PATH="/usr/bin/minizinc"
    echo "✓ MiniZinc found: $MINIZINC_PATH"
elif [ -d "$HOME/Documents/MiniZincIDE/bin" ]; then
    if [ -f "$HOME/Documents/MiniZincIDE/bin/minizinc" ]; then
        MINIZINC_PATH="$HOME/Documents/MiniZincIDE/bin/minizinc"
        echo "✓ MiniZinc found: $MINIZINC_PATH"
    fi
else
    echo "⚠ Warning: MiniZinc not found in common locations"
    echo "  The application will try to use the system default"
fi

# Create .env file if MiniZinc path was found
if [ -n "$MINIZINC_PATH" ]; then
    echo "Creating .env configuration file..."
    echo "MINIZINC_BIN_PATH=$MINIZINC_PATH" > .env
    echo "✓ Configuration saved to .env"
fi

echo ""
echo "====================================="
echo "Setup complete!"
echo "====================================="
echo ""
echo "To start the application:"
echo "  1. Activate the virtual environment:"
echo "     source venv/bin/activate"
echo "  2. Run the application:"
echo "     python app.py"
echo "  3. Open your browser at:"
echo "     http://localhost:8080"
echo ""
if [ -z "$MINIZINC_PATH" ]; then
    echo "⚠ Note: Make sure MiniZinc is installed and in your PATH!"
    echo "   You can download it from: https://www.minizinc.org/software.html"
fi
echo "====================================="
