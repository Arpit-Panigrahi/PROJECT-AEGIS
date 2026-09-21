# Project Aegis — One-Click Build Script for PowerShell
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   PROJECT AEGIS -- BUILDING SUBSYSTEM VIA WSL (FEDORA LINUX)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

wsl -d FedoraLinux-42 bash /mnt/c/Users/arpit/Desktop/aegis/build.sh

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "======================================================================" -ForegroundColor Green
    Write-Host "[+] BUILD SUCCESSFUL!" -ForegroundColor Green
    Write-Host "======================================================================" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "[-] BUILD FAILED! Check error output above." -ForegroundColor Red
}
