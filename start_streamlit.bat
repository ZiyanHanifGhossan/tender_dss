@echo off
REM Start Streamlit using the project's virtual environment Python (Windows cmd)
set SCRIPT_DIR=%~dp0

REM If venv missing, create and install requirements
if not exist "%SCRIPT_DIR%\.venv\Scripts\python.exe" (
  echo Virtualenv not found. Creating and installing requirements...
  python -m venv "%SCRIPT_DIR%\.venv"
  "%SCRIPT_DIR%\.venv\Scripts\python.exe" -m pip install --upgrade pip
  "%SCRIPT_DIR%\.venv\Scripts\python.exe" -m pip install -r "%SCRIPT_DIR%requirements.txt"
)

REM Ensure requirements are installed (idempotent)
"%SCRIPT_DIR%\.venv\Scripts\python.exe" -m pip install -r "%SCRIPT_DIR%requirements.txt"

echo Starting Streamlit with project venv...
"%SCRIPT_DIR%\.venv\Scripts\python.exe" -m streamlit run "%SCRIPT_DIR%app.py" %*
