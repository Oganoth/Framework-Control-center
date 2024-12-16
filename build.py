import os
import shutil
import subprocess
import sys

def check_requirements():
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build_executable():
    print("Building executable...")
    
    # Create build and dist directories if they don't exist
    if not os.path.exists("build"):
        os.makedirs("build")
    if not os.path.exists("dist"):
        os.makedirs("dist")
    
    # PyInstaller command
    pyinstaller_command = [
        "pyinstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        "--icon=assets/icon.ico",
        "--add-data=assets;assets/",
        "--add-data=ryzenadj;ryzenadj/",
        "--name=Framework_Laptop_Hub",
        "framework_laptop_hub.py"
    ]
    
    subprocess.check_call(pyinstaller_command)

def build_installer():
    print("Building installer...")
    # Check if NSIS is installed
    nsis_path = r"C:\Program Files (x86)\NSIS\makensis.exe"
    if not os.path.exists(nsis_path):
        print("Error: NSIS not found. Please install NSIS first.")
        print("Download from: https://nsis.sourceforge.io/Download")
        sys.exit(1)
    
    # Run NSIS compiler
    subprocess.check_call([nsis_path, "installer.nsi"])

def main():
    print("Starting build process...")
    
    # Check and install requirements
    check_requirements()
    
    # Build executable
    build_executable()
    
    # Build installer
    build_installer()
    
    print("Build completed successfully!")

if __name__ == "__main__":
    main() 