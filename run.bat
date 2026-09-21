@echo off
setlocal
echo ======================================================================
echo    PROJECT AEGIS -- LAUNCHING OPERATIONS DASHBOARD
echo ======================================================================
echo.
echo [*] Opening Dashboard in browser at: http://localhost:8080
start http://localhost:8080
echo [*] Starting Python backend server inside WSL...
echo.
wsl -d FedoraLinux-42 bash /mnt/c/Users/arpit/Desktop/aegis/run.sh
pause
