@echo off
echo Testing Framework Hub build...

REM Vérifier l'existence de l'exécutable
if not exist "dist\Framework_Hub\Framework_Hub.exe" (
    echo ERROR: Executable not found!
    exit /b 1
)

REM Vérifier les dossiers requis
if not exist "dist\Framework_Hub\assets" echo ERROR: Missing assets folder
if not exist "dist\Framework_Hub\libs" echo ERROR: Missing libs folder
if not exist "dist\Framework_Hub\ryzenadj" echo ERROR: Missing ryzenadj folder

REM Vérifier les fichiers de configuration
if not exist "dist\Framework_Hub\battery_config.json" echo ERROR: Missing battery_config.json
if not exist "dist\Framework_Hub\config.json" echo ERROR: Missing config.json
if not exist "dist\Framework_Hub\settings.json" echo ERROR: Missing settings.json
if not exist "dist\Framework_Hub\translations.py" echo ERROR: Missing translations.py

REM Vérifier les icônes
if not exist "dist\Framework_Hub\assets\logo.ico" echo ERROR: Missing logo.ico
if not exist "dist\Framework_Hub\assets\tray_icon.png" echo ERROR: Missing tray_icon.png
if not exist "dist\Framework_Hub\assets\error_icon.png" echo ERROR: Missing error_icon.png
if not exist "dist\Framework_Hub\assets\info_icon.png" echo ERROR: Missing info_icon.png

echo Test complete!
pause 