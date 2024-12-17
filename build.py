import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_requirements():
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def clean_directories():
    print("Cleaning build directories...")
    directories = ['build', 'dist']
    for directory in directories:
        if os.path.exists(directory):
            shutil.rmtree(directory)

def check_assets():
    print("Checking assets...")
    assets_dir = Path("assets")
    if not assets_dir.exists():
        print("Error: assets directory not found!")
        sys.exit(1)

    required_assets = [
        "logo.ico",
        "home.png",
        "tasks.png",
        "keyboard.png",
        "setting.png",
        "main.png"
    ]

    missing_assets = []
    for asset in required_assets:
        if not (assets_dir / asset).exists():
            missing_assets.append(asset)

    if missing_assets:
        print("Error: The following required assets are missing:")
        for asset in missing_assets:
            print(f"  - {asset}")
        sys.exit(1)

def copy_ryzenadj_files():
    print("Copying RyzenADJ files...")
    ryzenadj_dir = Path("ryzenadj")
    if not ryzenadj_dir.exists():
        print("Error: ryzenadj directory not found!")
        sys.exit(1)

    required_files = [
        "libryzenadj.dll",
        "WinRing0x64.sys",
        "pmtable-example.py"
    ]

    for file in required_files:
        if not (ryzenadj_dir / file).exists():
            print(f"Error: Required file {file} not found in ryzenadj directory!")
            sys.exit(1)

def copy_directory_contents(src_dir, dst_dir):
    """Copy all contents from src_dir to dst_dir"""
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir)
    
    for item in os.listdir(src_dir):
        src_item = os.path.join(src_dir, item)
        dst_item = os.path.join(dst_dir, item)
        if os.path.isdir(src_item):
            shutil.copytree(src_item, dst_item, dirs_exist_ok=True)
        else:
            shutil.copy2(src_item, dst_item)

def build_executable():
    print("Building executable...")
    
    # Check required directories and files
    check_assets()
    copy_ryzenadj_files()
    
    # Create spec file content
    spec_content = """# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['framework_laptop_hub.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Framework_Laptop_Hub',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/logo.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Framework_Laptop_Hub'
)
"""

    # Write spec file
    with open('Framework_Laptop_Hub.spec', 'w') as f:
        f.write(spec_content)

    # Run PyInstaller with the spec file
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "Framework_Laptop_Hub.spec"
    ]
    
    print("Running PyInstaller...")
    try:
        subprocess.run(cmd, check=True)
        print("Build completed successfully!")
        
        # Get the build directory
        dist_path = Path("dist") / "Framework_Laptop_Hub"
        
        # Manually copy required directories and files
        print("Copying assets and required files...")
        directories_to_copy = {
            "assets": "assets",
            "ryzenadj": "ryzenadj",
            "fonts": "fonts"
        }
        
        files_to_copy = [
            "settings.json",
            "translations.py",
            "laptop_models.py",
            "language_manager.py"
        ]
        
        # Copy directories
        for src, dst in directories_to_copy.items():
            src_path = Path(src)
            dst_path = dist_path / dst
            if src_path.exists():
                print(f"Copying {src} to {dst_path}")
                copy_directory_contents(src_path, dst_path)
        
        # Copy individual files
        for file in files_to_copy:
            src_file = Path(file)
            if src_file.exists():
                print(f"Copying {file} to {dist_path}")
                shutil.copy2(src_file, dist_path)
        
        # Verify the assets
        assets_path = dist_path / "assets"
        if not assets_path.exists() or not any(assets_path.iterdir()):
            print("Warning: Assets directory in build appears to be empty!")
        else:
            print("Assets verified successfully!")
            
    except subprocess.CalledProcessError as e:
        print(f"Error during build: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error during post-build file copying: {e}")
        sys.exit(1)

def main():
    print("Starting build process...")
    
    # Clean old build files
    clean_directories()
    
    # Check requirements
    check_requirements()
    
    # Build executable
    build_executable()

if __name__ == "__main__":
    main() 