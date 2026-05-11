#!/bin/bash
# Startup script for AI Research Assistant on Linux/Mac
# Starts both backend API and Streamlit frontend

echo ""
echo "========================================"
echo "AI Research Assistant - Startup"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    exit 1
fi

echo "[1/3] Checking dependencies..."
python3 -m pip show fastapi > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "ERROR: Dependencies not installed. Run: pip install -r requirements.txt"
    exit 1
fi

echo "[2/3] Starting Backend API (port 8000)..."
python3 -m app.main &
BACKEND_PID=$!
echo "Backend PID: $BACKEND_PID"
sleep 3

echo "[3/3] Starting Streamlit Frontend (port 8501)..."
streamlit run frontend/app.py &
FRONTEND_PID=$!
echo "Frontend PID: $FRONTEND_PID"

echo ""
echo "========================================"
echo "✅ AI Research Assistant Started!"
echo "========================================"
echo ""
echo "Frontend: http://localhost:8501"
echo "Backend:  http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
