@echo off
echo Building Framework Hub Mini...

REM Vérifier l'existence de l'environnement virtuel
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activer l'environnement virtuel
call venv\Scripts\activate

REM Installer/Mettre à jour les dépendances
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

REM Nettoyer les dossiers précédents
echo Cleaning previous build...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

REM Vérifier les fichiers nécessaires
echo Checking required files...
call check_assets.bat

REM Créer l'exécutable avec PyInstaller
echo Building executable...
pyinstaller mini.spec

REM Vérifier si le build a réussi
if not exist "dist\Framework_Hub\Framework_Hub.exe" (
    echo Build failed!
    pause
    exit /b 1
)

REM Copier les fichiers nécessaires
echo Copying required files...
xcopy /s /y assets dist\Framework_Hub\assets\
xcopy /s /y ryzenadj dist\Framework_Hub\ryzenadj\
xcopy /s /y libs dist\Framework_Hub\libs\
copy battery_config.json dist\Framework_Hub\
copy config.json dist\Framework_Hub\
copy settings.json dist\Framework_Hub\
copy translations.py dist\Framework_Hub\
copy LICENSE dist\Framework_Hub\
copy README.md dist\Framework_Hub\
copy RELEASE_NOTES.md dist\Framework_Hub\

echo Build complete!
echo Testing executable...
cd dist\Framework_Hub
start "" "Framework_Hub.exe"
cd ..\..
pause 