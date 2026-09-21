@echo off
setlocal
echo ======================================================================
echo    PROJECT AEGIS -- BUILDING SUBSYSTEM VIA WSL (FEDORA LINUX)
echo ======================================================================
echo.

wsl -d FedoraLinux-42 bash /mnt/c/Users/arpit/Desktop/aegis/build.sh

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo [+] BUILD SUCCESSFUL!
    echo ======================================================================
) else (
    echo.
    echo [-] BUILD FAILED! Please inspect errors above.
)

pause
