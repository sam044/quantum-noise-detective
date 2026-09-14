@echo off
set "QND_PYTHON=%USERPROFILE%\.venvs\quantum-noise-detective\Scripts\python.exe"
if not exist "%QND_PYTHON%" (
  echo The project Python environment is missing. See docs\SETUP.md.
  pause
  exit /b 1
)
echo Starting Quantum Noise Detective in the background...
"%QND_PYTHON%" "%~dp0launch.py" --background
if errorlevel 1 pause
