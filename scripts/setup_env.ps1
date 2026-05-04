# PowerShell script to create virtual environment and install requirements
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Push-Location $scriptDir

if (-Not (Test-Path -Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

$venvPython = Join-Path $scriptDir ".venv\Scripts\python.exe"
Write-Host "Upgrading pip and installing requirements using: $venvPython"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r (Join-Path $scriptDir "..\requirements.txt")

Write-Host "Environment setup complete. You can run Streamlit with:`$venvPython -m streamlit run app.py` or use .\start_streamlit.ps1"
Pop-Location
