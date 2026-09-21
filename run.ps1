# Project Aegis — One-Click Launch Script for PowerShell
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   PROJECT AEGIS -- LAUNCHING OPERATIONS DASHBOARD" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[*] Launching browser at: http://localhost:8080" -ForegroundColor Green
Start-Process "http://localhost:8080"
Write-Host "[*] Starting Python backend server inside WSL..." -ForegroundColor Yellow
Write-Host ""
wsl -d FedoraLinux-42 bash /mnt/c/Users/arpit/Desktop/aegis/run.sh
