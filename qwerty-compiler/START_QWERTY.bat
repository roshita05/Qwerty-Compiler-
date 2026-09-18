@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
    set "QW_PY=py -3"
) else (
    set "QW_PY=python"
)
%QW_PY% -c "import sys; raise SystemExit(0 if sys.version_info >= (3,11) else 1)" >nul 2>nul
if errorlevel 1 (
    echo QWERTY needs Python 3.11 or newer.
    echo Install an approved Python version, reopen this folder, and try again.
    pause
    exit /b 1
)
echo.
echo Starting QWERTY Language Studio...
echo Open http://127.0.0.1:8765 in your browser after the server starts.
echo Keep this terminal open. Press Ctrl+C to stop.
echo.
%QW_PY% -m qwerty web
pause
