@echo off
REM Startup script for AI Research Assistant on Windows
REM Starts both backend API and Streamlit frontend

echo.
echo ========================================
echo AI Research Assistant - Startup
echo ========================================
echo.

set "PROJECT_ROOT=%~dp0"
set "BACKEND_PY=%PROJECT_ROOT%.venv314\Scripts\python.exe"
set "FRONTEND_PY=%PROJECT_ROOT%.venv314\Scripts\python.exe"

if not exist "%BACKEND_PY%" (
    set "BACKEND_PY=python"
)

if not exist "%FRONTEND_PY%" (
    set "FRONTEND_PY=python"
)

echo [1/3] Checking dependencies...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo ERROR: Dependencies not installed. Run: pip install -r requirements.txt
    pause
    exit /b 1
)

echo [2/3] Starting Backend API (port 8000)...
start cmd /k "cd /d \"%PROJECT_ROOT%\" && set PYTHONPATH=%PROJECT_ROOT% && \"%BACKEND_PY%\" -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
echo Backend starting... (waiting 3 seconds)
timeout /t 3 /nobreak >nul

echo [3/3] Starting Streamlit Frontend (port 8501)...
start cmd /k "cd /d \"%PROJECT_ROOT%\" && \"%FRONTEND_PY%\" -m streamlit run frontend/app.py"

echo.
echo ========================================
echo ✅ AI Research Assistant Started!
echo ========================================
echo.
echo Frontend: http://localhost:8501
echo Backend:  http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.
echo Close the backend window to stop the API
echo Close the frontend window to stop Streamlit
echo.
pause
