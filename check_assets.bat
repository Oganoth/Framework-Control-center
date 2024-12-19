@echo off
echo Checking required files...

REM Vérifier les dossiers
if not exist "assets" echo Missing assets folder
if not exist "libs" echo Missing libs folder
if not exist "ryzenadj" echo Missing ryzenadj folder
if not exist "screenshots" echo Missing screenshots folder

REM Vérifier les fichiers de configuration
if not exist "battery_config.json" echo Missing battery_config.json
if not exist "config.json" echo Missing config.json
if not exist "settings.json" echo Missing settings.json

REM Vérifier les fichiers Python
if not exist "mini.py" echo Missing mini.py
if not exist "translations.py" echo Missing translations.py
if not exist "language_manager.py" echo Missing language_manager.py
if not exist "laptop_models.py" echo Missing laptop_models.py

REM Vérifier les fichiers de documentation
if not exist "LICENSE" echo Missing LICENSE
if not exist "README.md" echo Missing README.md
if not exist "RELEASE_NOTES.md" echo Missing RELEASE_NOTES.md

REM Vérifier les icônes
if not exist "assets\logo.ico" echo Missing assets\logo.ico
if not exist "assets\tray_icon.png" echo Missing assets\tray_icon.png
if not exist "assets\error_icon.png" echo Missing assets\error_icon.png
if not exist "assets\info_icon.png" echo Missing assets\info_icon.png

echo Check complete!
pause 