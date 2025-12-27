#!/bin/bash

# CONNECT LAB ANALYSIS PIPELINE (CLAP) - Launcher

# Setup Paths
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ENV_DIR="$DIR/complementary_files/clap_env"
REQ_FILE="$DIR/complementary_files/requirements.txt"
MAIN_SCRIPT="$DIR/XC_CLAP_MAIN.py"

# Function to test for tkinter support
check_tkinter() {
    "$1" -c "import tkinter" &> /dev/null
    return $?
}

echo "=========================================="
echo "   CONNECT LAB ANALYSIS PIPELINE (CLAP)   "
echo "=========================================="

# Find a valid Python executable
CANDIDATES=("python3.13" "python3.12" "python3" "/usr/bin/python3")
CHOSEN_PYTHON=""

for py in "${CANDIDATES[@]}"; do
    if command -v "$py" &> /dev/null; then
        if check_tkinter "$py"; then
            echo "Found valid Python at: $py"
            CHOSEN_PYTHON="$py"
            break
        else
            echo "Skipping $py (Missing tkinter support)"
        fi
    fi
done

# Error handling if no valid Python is found
if [ -z "$CHOSEN_PYTHON" ]; then
    echo ""
    echo "CRITICAL ERROR: No suitable Python found."
    echo "CLAP requires Python with Tkinter support."
    echo ""
    echo "TO FIX THIS:"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Run: brew install python-tk"
    else
        echo "Run: sudo apt-get install python3-tk"
    fi
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Auto-install environment if missing
if [ ! -d "$ENV_DIR" ]; then
    echo "First run detected. Building environment..."
    
    "$CHOSEN_PYTHON" -m venv "$ENV_DIR"
    "$ENV_DIR/bin/pip" install --upgrade pip &> /dev/null
    
    if [ -f "$REQ_FILE" ]; then
        echo "Installing dependencies..."
        "$ENV_DIR/bin/pip" install -r "$REQ_FILE"
    fi
    
    echo "Setup complete."
fi

# Launch App
echo "Launching CLAP..."
"$ENV_DIR/bin/python3" "$MAIN_SCRIPT"