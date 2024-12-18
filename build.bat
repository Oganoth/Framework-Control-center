@echo off
echo Building Framework Laptop Hub...

REM Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH
    exit /b 1
)

REM Create and activate virtual environment
echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt
pip install pyinstaller

REM Run check_assets.bat to ensure all assets are present
echo Checking assets...
call check_assets.bat

REM Clean previous builds
echo Cleaning previous builds...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

REM Build executable
echo Building executable...
pyinstaller --clean mini.spec

REM Check if build was successful
if %ERRORLEVEL% NEQ 0 (
    echo Build failed!
    exit /b 1
)

REM Move the executable to the final directory
echo Creating output directory...
move "dist\Framework_Hub.exe" "dist\Framework_Hub.exe.tmp"
rmdir /s /q "dist\Framework_Hub" 2>nul
mkdir "dist\Framework_Hub"
move "dist\Framework_Hub.exe.tmp" "dist\Framework_Hub\mini.exe"

REM Copy all required files and folders
echo Copying required files...
xcopy /E /I /Y "assets" "dist\Framework_Hub\assets"
xcopy /E /I /Y "fonts" "dist\Framework_Hub\fonts"
xcopy /E /I /Y "ryzenadj" "dist\Framework_Hub\ryzenadj"

REM Copy configuration files
echo Copying configuration files...
copy "battery_config.json" "dist\Framework_Hub\"
copy "config.json" "dist\Framework_Hub\"
copy "settings.json" "dist\Framework_Hub\"
copy "LICENSE" "dist\Framework_Hub\"
copy "README.md" "dist\Framework_Hub\"
copy "RELEASE_NOTES.md" "dist\Framework_Hub\"

echo Build complete! Output is in dist\Framework_Hub\

REM Build the installer
echo Building installer...
cd installer
call build_installer.bat
cd ..

REM Deactivate virtual environment
deactivate

echo Build and installer creation complete!
echo You can find the installer at: dist\Framework_Hub_Setup.exe

pause 