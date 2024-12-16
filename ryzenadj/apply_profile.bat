@echo off
echo Applying Performance profile...
cd /d "%~dp0"
"C:\Users\johnd\Documents\TEST\app\ryzenadj\ryzenadj.exe" --stapm-limit 65000 --fast-limit 70000 --slow-limit 65000 --tctl-temp 100
if %ERRORLEVEL% EQU 0 (
    echo Profile applied successfully
    exit /b 0
) else (
    echo Failed to apply profile
    exit /b 1
)
