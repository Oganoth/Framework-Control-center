@echo off
setlocal EnableDelayedExpansion

echo Building Framework Laptop Hub...

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if PowerShell is available
powershell -Command "exit" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: PowerShell is not available
    pause
    exit /b 1
)

REM Check if System.Drawing is available in PowerShell
powershell -Command "Add-Type -AssemblyName System.Drawing" >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: System.Drawing assembly is not available in PowerShell
    pause
    exit /b 1
)

REM Check if NSIS is installed
if not exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    echo ERROR: NSIS is not installed in the default location
    echo Please install NSIS from https://nsis.sourceforge.io/Download
    pause
    exit /b 1
)

REM Clean previous build
if exist "dist" (
    echo Cleaning previous build...
    rd /s /q "dist"
)
if exist "build" (
    rd /s /q "build"
)
if exist "Framework_Laptop_Hub_Setup.exe" (
    del "Framework_Laptop_Hub_Setup.exe"
)

REM Check and create required assets
echo Checking and creating required assets...
call check_assets.bat
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to check/create assets
    pause
    exit /b 1
)

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install requirements
    pause
    exit /b 1
)

REM Build executable
echo Building executable...
python build.py
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to build executable
    pause
    exit /b 1
)

REM Verify build directory and executable
if not exist "dist\Framework_Laptop_Hub" (
    echo ERROR: Build directory not found
    pause
    exit /b 1
)
if not exist "dist\Framework_Laptop_Hub\Framework_Laptop_Hub.exe" (
    echo ERROR: Executable not found in build directory
    pause
    exit /b 1
)

REM Create installer
echo Creating installer...
"C:\Program Files (x86)\NSIS\makensis.exe" installer.nsi
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to create installer
    pause
    exit /b 1
)

REM Verify installer was created
if exist "Framework_Laptop_Hub_Setup.exe" (
    echo Build complete!
    echo Installer created: Framework_Laptop_Hub_Setup.exe
    echo.
    echo You can now run Framework_Laptop_Hub_Setup.exe to install the application.
) else (
    echo ERROR: Installer creation failed
    pause
    exit /b 1
)

pause