@echo off
echo Building installer...

REM Vérifier que le dossier dist existe
if not exist "dist\Framework_Hub\Framework_Hub.exe" (
    echo ERREUR: Framework_Hub.exe n'existe pas dans le dossier dist!
    echo Lancez d'abord le build.bat pour créer l'executable
    pause
    exit /b 1
)

REM Chemin vers le compilateur Inno Setup
set ISCC="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

REM Compiler l'installateur
%ISCC% installer.iss

if errorlevel 1 (
    echo ERREUR: La compilation de l'installateur a échoué!
    pause
    exit /b 1
)

echo Installation package created successfully!
pause 