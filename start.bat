@echo off
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found on this computer.
  echo Install Python 3 and make sure "Add Python to PATH" is enabled.
  pause
  exit /b 1
)

python server.py
if errorlevel 1 (
  echo.
  echo LYMEC Gender Watch stopped because of an error.
  pause
)
