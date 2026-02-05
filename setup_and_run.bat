@echo off
title AI Medical Assistant Setup & Launcher
color 0A
echo ===================================================
echo 🚀 AI MEDICAL ASSISTANT - SMART SETUP
echo ===================================================

REM === STEP 1: Check Python ===
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo ❌ Python not found! Please install Python 3.10+ and add it to PATH.
    pause
    exit /b
)

REM === STEP 2: Create virtual environment if not exists ===
if not exist venv1 (
    echo 🧩 Creating virtual environment...
    python -m venv venv1
) else (
    echo ✅ Virtual environment already exists.
)

REM === STEP 3: Activate environment ===
call venv1\Scripts\activate

REM === STEP 4: Upgrade pip silently ===
echo 📦 Checking Python package manager...
python -m pip install --upgrade pip >nul

REM === STEP 5: Auto-generate or update requirements.txt ===
echo 🧠 Updating requirements.txt ...
pip freeze > requirements.txt

REM === STEP 6: Install dependencies ===
echo ⚙️ Installing/Updating dependencies (this may take a while)...
pip install -r requirements.txt

REM === STEP 7: Ensure .env exists ===
if not exist .env (
    echo ⚠️ Creating new .env file...
    echo HF_AUTH_TOKEN= > .env
    echo Please paste your Hugging Face token in .env later.
)

REM === STEP 8: Run migrations ===
echo 🗃️ Applying database migrations...
python manage.py makemigrations
python manage.py migrate

REM === STEP 9: Optionally create superuser ===
set /p CREATEADMIN=Do you want to create an admin account (y/n)?
if /I "%CREATEADMIN%"=="y" (
    python manage.py createsuperuser
)

REM === STEP 10: Start the server ===
echo ===================================================
echo ✅ SETUP COMPLETE! STARTING SERVER...
echo ===================================================
echo 🌐 Open http://127.0.0.1:8000 in your browser.
echo ===================================================

python manage.py runserver

pause
