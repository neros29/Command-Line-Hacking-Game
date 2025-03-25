@echo off
REM Batch file to activate the virtual environment and install requirements.txt

REM Check if the virtual environment exists
if not exist ".myenv\Scripts\activate.bat" (
    echo Virtual environment not found. Creating it...
    python -m venv .myenv
)

REM Activate the virtual environment
call .myenv\Scripts\activate.bat

REM Check if requirements.txt exists
if not exist "requirements.txt" (
    echo requirements.txt not found. Please create it first.
    pause
    exit /b 1
)

REM Install dependencies from requirements.txt
pip install -r requirements.txt

echo Dependencies installed successfully.
pause
