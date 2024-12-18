@echo off
echo Building Framework Hub Installer...

REM Check if NSIS is installed
if not exist "%PROGRAMFILES(X86)%\NSIS\makensis.exe" (
    echo Error: NSIS is not installed!
    echo Please download and install NSIS from https://nsis.sourceforge.io/Download
    exit /b 1
)

REM Build the installer
"%PROGRAMFILES(X86)%\NSIS\makensis.exe" /V4 installer.nsi

if errorlevel 1 (
    echo Error: Installer creation failed!
    exit /b 1
) else (
    echo Installer created successfully!
    echo You can find it at: dist\Framework_Hub_Setup.exe
) 