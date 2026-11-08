#!/usr/bin/env bash
# Run this file to set up the python environment and other requirements on Ubuntu/Linux
# Usage: bash setup.sh   (or: chmod +x setup.sh && ./setup.sh)

# Stop on the first error
set -e

# Create the virtual environment folder for python
echo "Creating Directories"
echo "--------------------------------------"
mkdir -p .venv
mkdir -p data

echo "Creating Python Virtual Environment"
echo "--------------------------------------"
# On Ubuntu the venv module is packaged separately; install it if missing:
#   sudo apt update && sudo apt install -y python3 python3-venv python3-pip
set -x
python3 -m venv .venv/pyenv
source .venv/pyenv/bin/activate
set +x

echo "Upgrading pip"
echo "--------------------------------------"
set -x
python -m pip install --upgrade pip
set +x

echo "Installing Python Packages"
echo "--------------------------------------"
set -x
python -m pip install -r setup/requirements.txt
set +x

echo "Setup Complete"
echo "--------------------------------------"
read -n 1 -s -r -p "Press any key to continue..."
echo
