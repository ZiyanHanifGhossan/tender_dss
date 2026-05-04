# Start Streamlit using the project's virtual environment Python (PowerShell)
$PSScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $PSScriptRoot

# If venv missing, create it and install requirements
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-Not (Test-Path -Path $venvPython)) {
    Write-Host "Virtualenv not found. Creating and installing requirements..."
    python -m venv .venv
    & $venvPython -m pip install --upgrade pip
    & $venvPython -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")
}

# Ensure requirements installed (idempotent)
& $venvPython -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")

Write-Host "Starting Streamlit with project venv: $venvPython"
& $venvPython -m streamlit run "app.py"
Pop-Location
