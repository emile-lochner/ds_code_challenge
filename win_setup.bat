:: Run this file to set up the python environment and other requirements on a Windows computer
@echo off

:: Create the virtual environment folder for python
echo --------------------------------------
echo Creating Directories
echo --------------------------------------
mkdir .venv
mkdir data

echo --------------------------------------
echo Creating Python Virtual Environment
echo --------------------------------------
@echo on
python -m venv .venv\pyenv
call .venv\pyenv\Scripts\activate.bat
@echo off

echo --------------------------------------
echo Upgrading pip
echo --------------------------------------
@echo on
python -m pip install --upgrade pip
@echo off

echo --------------------------------------
echo Installing Python Packages
echo --------------------------------------
:: pip install -r setup\requirements.txt
@echo on
python -m pip install -r setup\requirements.txt
@echo off

echo --------------------------------------
echo Downloading Data
echo --------------------------------------
curl -L -O --output-dir "data" "https://cct-ds-code-challenge-input-data.s3.af-south-1.amazonaws.com/city-hex-polygons-8.geojson"

echo --------------------------------------
echo Setup Complete
echo --------------------------------------
pause