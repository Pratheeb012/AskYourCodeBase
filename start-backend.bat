@echo off
echo.
echo  ============================================
echo   Ask Your Codebase - Backend Startup
echo  ============================================
echo.

cd /d "%~dp0backend"

if not exist ".env" (
    echo  [!] .env not found. Copying from .env.example...
    copy .env.example .env
    echo  [!] Please edit backend\.env with your OpenAI API key and DB URL
    echo  [!] Then re-run this script.
    pause
    exit /b 1
)

if not exist "venv" (
    echo  [*] Creating virtual environment...
    python -m venv venv
)

echo  [*] Activating virtual environment...
call venv\Scripts\activate

echo  [*] Installing dependencies...
pip install -r requirements.txt -q

echo  [*] Starting FastAPI server on http://localhost:8000
echo  [*] API docs at http://localhost:8000/api/docs
echo.
uvicorn app.main:app --reload --port 8000 --host 0.0.0.0
