@echo off
echo Applying Performance profile...
cd /d "%~dp0"
"D:\Python\Framework-Hub\dist\Framework_Laptop_Hub\ryzenadj\ryzenadj.exe" --stapm-limit 120000 --fast-limit 140000 --slow-limit 120000 --tctl-temp 100 --cHTC-temp 100 --apu-skin-temp 50 --vrm-current 200000 --vrmmax-current 200000 --vrmsoc-current 200000 --vrmsocmax-current 200000 --vrmgfx-current 200000 --Win-Power 2
if %ERRORLEVEL% EQU 0 (
    echo Profile applied successfully
    exit /b 0
) else (
    echo Failed to apply profile
    exit /b 1
)
