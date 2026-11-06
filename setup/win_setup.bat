:: Run this file to set up the python environment and other requirements on a Windows computer
@echo off

:: Create the virtual environment folder for python
echo --------------------------------------
echo Creating Directories
echo --------------------------------------
mkdir .venv
mkdir data

echo --------------------------------------
echo Upgrading pip
echo --------------------------------------
python -m pip install --upgrade pip

echo --------------------------------------
echo Creating Python Virtual Environment
echo --------------------------------------
python -m venv .venv\pyenv

Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\pyenv\Scripts\activate.bat

echo --------------------------------------
echo Installing Python Packages
echo --------------------------------------
pip install -r setup\requirements.txt

:: End of script
echo --------------------------------------
echo Setup Complete
echo --------------------------------------
pause