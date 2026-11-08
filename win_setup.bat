:: Run this file to set up the python environment and other requirements on a Windows computer
@echo off

:: Create the virtual environment folder for python
echo Creating Directories
echo --------------------------------------
mkdir .venv
mkdir data

echo Creating Python Virtual Environment
echo --------------------------------------
@echo on
python -m venv .venv\pyenv
call .venv\pyenv\Scripts\activate.bat
@echo off

echo Upgrading pip
echo --------------------------------------
@echo on
python -m pip install --upgrade pip
@echo off

echo Installing Python Packages
echo --------------------------------------
@echo on
python -m pip install -r setup\requirements.txt
@echo off

echo Setup Complete
echo --------------------------------------
pause