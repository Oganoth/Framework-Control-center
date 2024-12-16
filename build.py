import PyInstaller.__main__
import os
import shutil
import sys
from pathlib import Path

def build_exe():
    try:
        print("Starting build process...")
        
        # Get the script directory
        script_dir = Path(__file__).parent.absolute()
        os.chdir(script_dir)
        
        print(f"Working directory: {script_dir}")
        
        # Clean previous builds
        for dir_name in ['build', 'dist']:
            dir_path = script_dir / dir_name
            if dir_path.exists():
                print(f"Cleaning {dir_path}")
                shutil.rmtree(dir_path)
        
        # Ensure required directories exist
        required_dirs = ['assets', 'fonts', 'ryzenadj']
        for dir_name in required_dirs:
            dir_path = script_dir / dir_name
            dir_path.mkdir(exist_ok=True)
            print(f"Ensured directory exists: {dir_path}")
        
        # Check for required files
        required_files = [
            'framework_laptop_hub.py',
            'translations.py',
            'language_manager.py',
            'settings.json'
        ]
        
        # Check for required assets
        required_assets = [
            'assets/logo.ico',
            'assets/home.png',
            'assets/tasks.png',
            'assets/keyboard.png',
            'assets/setting.png',
            'assets/main.png'
        ]
        
        # Check for required fonts
        required_fonts = [
            'fonts/Ubuntu-Regular.ttf',
            'fonts/Ubuntu-Medium.ttf',
            'fonts/Ubuntu-Bold.ttf',
            'fonts/Ubuntu-Light.ttf',
            'fonts/Ubuntu-Italic.ttf',
            'fonts/Ubuntu-MediumItalic.ttf',
            'fonts/Ubuntu-BoldItalic.ttf',
            'fonts/Ubuntu-LightItalic.ttf'
        ]
        
        # Check all required files
        for file_path in required_files + required_assets + required_fonts:
            if not (script_dir / file_path).exists():
                print(f"ERROR: Required file not found: {file_path}")
                return False
        
        # PyInstaller command line arguments
        args = [
            str(script_dir / 'framework_laptop_hub.py'),
            '--name=Framework_Laptop_Hub',
            '--onedir',
            '--windowed',
            f'--icon={script_dir}/assets/logo.ico',
            f'--add-data={script_dir}/assets;assets',
            f'--add-data={script_dir}/fonts;fonts',
            f'--add-data={script_dir}/ryzenadj;ryzenadj',
            f'--add-data={script_dir}/translations.py;.',
            f'--add-data={script_dir}/language_manager.py;.',
            f'--add-data={script_dir}/settings.json;.',
            '--hidden-import=PIL._tkinter_finder',
            '--hidden-import=queue',
            '--hidden-import=urllib.parse',
            '--hidden-import=http.client',
            '--hidden-import=urllib.request',
            '--hidden-import=json',
            '--clean',
            '--noconfirm',
            '--uac-admin',
        ]
        
        print("Running PyInstaller with arguments:", args)
        PyInstaller.__main__.run(args)
        
        # Copy assets to dist directory
        dist_dir = script_dir / 'dist' / 'Framework_Laptop_Hub'
        assets_dir = dist_dir / 'assets'
        fonts_dir = dist_dir / 'fonts'
        
        # Ensure directories exist in dist
        assets_dir.mkdir(exist_ok=True)
        fonts_dir.mkdir(exist_ok=True)
        
        # Copy assets
        for asset in required_assets:
            src = script_dir / asset
            dst = dist_dir / asset
            dst.parent.mkdir(exist_ok=True)
            if src.exists():
                shutil.copy2(src, dst)
                print(f"Copied {asset} to dist directory")
        
        # Copy fonts
        for font in required_fonts:
            src = script_dir / font
            dst = dist_dir / font
            dst.parent.mkdir(exist_ok=True)
            if src.exists():
                shutil.copy2(src, dst)
                print(f"Copied {font} to dist directory")
        
        print("Build complete! Executable created in:", dist_dir)
        return True
        
    except Exception as e:
        print(f"Error during build: {str(e)}", file=sys.stderr)
        return False

if __name__ == '__main__':
    success = build_exe()
    sys.exit(0 if success else 1) 