@echo off
title RTP AI Car Model
echo ========================================
echo    RTP AI Car Model - Starting App
echo ========================================
echo.

:: Change to project root directory
cd /d "%~dp0.."
cd streamlit || (
    echo ERROR: Could not change to streamlit directory!
    echo Please ensure the script is located in the correct path.
    pause
    exit /b 1
)

:: Check if main.py exists
if not exist "MapVisualize.py" (
    echo ERROR: main.py not found in current directory!
    echo Current directory: %CD%
    echo Please run this script from the project root or check file location.
    pause
    exit /b 1
)

:: Try different Python/Streamlit execution methods
if exist ".venv\Scripts\streamlit.exe" (
    echo [INFO] Using virtual environment streamlit...
    echo [INFO] Starting application on http://localhost:8501
    echo [INFO] If port 8501 is busy, Streamlit will try the next available port
    echo.
    ".venv\Scripts\streamlit.exe" run "MapVisualize.py" --server.port=8501
) else if exist ".venv\Scripts\python.exe" (
    echo [INFO] Using virtual environment python with streamlit module...
    echo [INFO] Starting application on http://localhost:8501
    echo [INFO] If port 8501 is busy, Streamlit will try the next available port
    echo.
    ".venv\Scripts\python.exe" -m streamlit run "MapVisualize.py" --server.port=8501
) else (
    echo [WARN] Virtual environment not found, using system python...
    echo [INFO] Starting application on http://localhost:8501
    echo [INFO] If port 8501 is busy, Streamlit will try the next available port
    echo.
    python -m streamlit run "MapVisualize.py" --server.port=8501
)

echo.
echo ========================================
echo Application stopped. Press any key to exit...
pause >nul