@echo off
setlocal
cd /d "%~dp0"
set ELECTRON_RUN_AS_NODE=
if not exist "node_modules\electron\dist\electron.exe" (
  echo Install the client dependencies with npm install first.
  pause
  exit /b 1
)
"node_modules\electron\dist\electron.exe" .
