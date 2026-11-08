#!/usr/bin/env bash
# Activate the virtual environment and run the main script (Ubuntu/Linux)
# Usage: bash run.sh   (or: chmod +x run.sh && ./run.sh)
 
# Run from the folder this script lives in, so relative paths work from anywhere
source .venv/pyenv/bin/activate
python src/main.py
 
read -n 1 -s -r -p "Press any key to continue..."
echo
 