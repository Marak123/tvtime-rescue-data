@echo off
REM TV Time Rescue - double-click launcher for Windows (run from source).
REM If you downloaded the ready-made tvtime-rescue-windows.exe you do NOT need this;
REM just run that exe instead.

setlocal
pushd "%~dp0.."

echo ==================================================================
echo   TV Time Rescue
echo ==================================================================
echo.

REM Find Python.
set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
  where python >nul 2>nul && set "PY=python"
)
if not defined PY (
  echo Python was not found on this computer.
  echo Please install Python 3 from https://www.python.org/downloads/
  echo and tick "Add Python to PATH" during setup, then run this file again.
  echo.
  pause
  popd
  exit /b 1
)

echo Making sure the requirements are installed (this is quick after the first time)...
%PY% -m pip install --quiet --disable-pip-version-check -r requirements.txt

echo.
%PY% run.py

echo.
pause
popd
endlocal
