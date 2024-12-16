<<<<<<< HEAD
@echo off
echo Checking required assets...

REM Create assets directory if it doesn't exist
if not exist "assets" (
    echo Creating assets directory...
    mkdir assets
)

REM Check for logo.ico
if not exist "assets\logo.ico" (
    echo WARNING: logo.ico not found in assets directory.
    echo Creating a default icon...
    
    REM Create a simple icon using PowerShell (all in one line)
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$bitmap = New-Object System.Drawing.Bitmap(32,32); $graphics = [System.Drawing.Graphics]::FromImage($bitmap); $graphics.Clear([System.Drawing.Color]::FromArgb(255,255,68,0)); $font = New-Object System.Drawing.Font('Arial',14,[System.Drawing.FontStyle]::Bold); $brush = [System.Drawing.Brushes]::White; $graphics.DrawString('F',$font,$brush,8,5); $bitmap.Save('assets/logo.png',[System.Drawing.Imaging.ImageFormat]::Png); $graphics.Dispose(); $bitmap.Dispose();"
    
    REM Convert PNG to ICO using PowerShell if ImageMagick is not available
    where magick >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        magick convert assets\logo.png assets\logo.ico
        del assets\logo.png
    ) else (
        echo WARNING: ImageMagick not found. Creating ICO directly with PowerShell...
        powershell -NoProfile -ExecutionPolicy Bypass -Command "$icon = [System.Drawing.Icon]::FromHandle((New-Object System.Drawing.Bitmap('assets/logo.png')).GetHicon()); $fileStream = [System.IO.File]::Create('assets/logo.ico'); $icon.Save($fileStream); $fileStream.Close(); $icon.Dispose();"
        del assets\logo.png
    )
)

REM Check for fonts directory
if not exist "fonts" (
    echo Creating fonts directory...
    mkdir fonts
)

REM Check for ryzenadj directory
if not exist "ryzenadj" (
    echo Creating ryzenadj directory...
    mkdir ryzenadj
)

REM Check for Ubuntu fonts
set "FONTS_MISSING="
for %%f in (Ubuntu-Regular.ttf Ubuntu-Medium.ttf Ubuntu-Bold.ttf Ubuntu-Light.ttf Ubuntu-Italic.ttf Ubuntu-MediumItalic.ttf Ubuntu-BoldItalic.ttf Ubuntu-LightItalic.ttf) do (
    if not exist "fonts\%%f" set "FONTS_MISSING=1"
)

if defined FONTS_MISSING (
    echo WARNING: Ubuntu fonts not found. Downloading...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "& { $webClient = New-Object System.Net.WebClient; $webClient.DownloadFile('https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-Regular.ttf', 'fonts/Ubuntu-Regular.ttf'); $webClient.DownloadFile('https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-Medium.ttf', 'fonts/Ubuntu-Medium.ttf'); $webClient.DownloadFile('https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-Bold.ttf', 'fonts/Ubuntu-Bold.ttf'); $webClient.DownloadFile('https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-Light.ttf', 'fonts/Ubuntu-Light.ttf'); $webClient.DownloadFile('https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-Italic.ttf', 'fonts/Ubuntu-Italic.ttf'); $webClient.DownloadFile('https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-MediumItalic.ttf', 'fonts/Ubuntu-MediumItalic.ttf'); $webClient.DownloadFile('https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-BoldItalic.ttf', 'fonts/Ubuntu-BoldItalic.ttf'); $webClient.DownloadFile('https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-LightItalic.ttf', 'fonts/Ubuntu-LightItalic.ttf'); }"
)

echo Asset check complete!
=======
@echo off
echo Checking required assets...

REM Create assets directory if it doesn't exist
if not exist "assets" (
    echo Creating assets directory...
    mkdir assets
)

REM Check for logo.ico
if not exist "assets\logo.ico" (
    echo WARNING: logo.ico not found in assets directory.
    echo Creating a default icon...
    
    REM Create a simple icon using PowerShell (all in one line)
    powershell -NoProfile -ExecutionPolicy Bypass -Command "$bitmap = New-Object System.Drawing.Bitmap(32,32); $graphics = [System.Drawing.Graphics]::FromImage($bitmap); $graphics.Clear([System.Drawing.Color]::FromArgb(255,255,68,0)); $font = New-Object System.Drawing.Font('Arial',14,[System.Drawing.FontStyle]::Bold); $brush = [System.Drawing.Brushes]::White; $graphics.DrawString('F',$font,$brush,8,5); $bitmap.Save('assets/logo.png',[System.Drawing.Imaging.ImageFormat]::Png); $graphics.Dispose(); $bitmap.Dispose();"
    
    REM Convert PNG to ICO using PowerShell if ImageMagick is not available
    where magick >nul 2>nul
    if %ERRORLEVEL% EQU 0 (
        magick convert assets\logo.png assets\logo.ico
        del assets\logo.png
    ) else (
        echo WARNING: ImageMagick not found. Creating ICO directly with PowerShell...
        powershell -NoProfile -ExecutionPolicy Bypass -Command "$icon = [System.Drawing.Icon]::FromHandle((New-Object System.Drawing.Bitmap('assets/logo.png')).GetHicon()); $fileStream = [System.IO.File]::Create('assets/logo.ico'); $icon.Save($fileStream); $fileStream.Close(); $icon.Dispose();"
        del assets\logo.png
    )
)

REM Check for fonts directory
if not exist "fonts" (
    echo Creating fonts directory...
    mkdir fonts
)

REM Check for ryzenadj directory
if not exist "ryzenadj" (
    echo Creating ryzenadj directory...
    mkdir ryzenadj
)

REM Check for Ubuntu fonts
set "FONTS_MISSING="
for %%f in (Ubuntu-Regular.ttf Ubuntu-Medium.ttf Ubuntu-Bold.ttf Ubuntu-Light.ttf Ubuntu-Italic.ttf Ubuntu-MediumItalic.ttf Ubuntu-BoldItalic.ttf Ubuntu-LightItalic.ttf) do (
    if not exist "fonts\%%f" set "FONTS_MISSING=1"
)

if defined FONTS_MISSING (
    echo WARNING: Ubuntu fonts not found. Downloading...
    powershell -NoProfile -ExecutionPolicy Bypass -Command "& { $webClient = New-Object System.Net.WebClient; $webClient.DownloadFile('https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-Regular.ttf', 'fonts/Ubuntu-Regular.ttf'); $webClient.DownloadFile('https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-Medium.ttf', 'fonts/Ubuntu-Medium.ttf'); $webClient.DownloadFile('https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-Bold.ttf', 'fonts/Ubuntu-Bold.ttf'); $webClient.DownloadFile('https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-Light.ttf', 'fonts/Ubuntu-Light.ttf'); $webClient.DownloadFile('https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-Italic.ttf', 'fonts/Ubuntu-Italic.ttf'); $webClient.DownloadFile('https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-MediumItalic.ttf', 'fonts/Ubuntu-MediumItalic.ttf'); $webClient.DownloadFile('https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-BoldItalic.ttf', 'fonts/Ubuntu-BoldItalic.ttf'); $webClient.DownloadFile('https://github.com/google/fonts/raw/main/ufl/ubuntu/Ubuntu-LightItalic.ttf', 'fonts/Ubuntu-LightItalic.ttf'); }"
)

echo Asset check complete!
>>>>>>> 8f8d397c7b484dbae0b69356bfd753ecb37b9d32
exit /b 0