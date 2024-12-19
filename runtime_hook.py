import os
import sys
import ctypes
from pathlib import Path

def add_dll_directory():
    try:
        if hasattr(os, 'add_dll_directory'):
            # Ajouter les dossiers système au PATH DLL
            system32_paths = [
                os.path.join(os.environ['SystemRoot'], 'System32'),
                os.path.join(os.environ['SystemRoot'], 'SysWOW64'),
                os.path.join(os.environ['SystemRoot'], 'WinSxS')
            ]
            
            for path in system32_paths:
                if os.path.exists(path):
                    os.add_dll_directory(path)
                    
            # Ajouter le dossier de l'application
            if getattr(sys, 'frozen', False):
                app_path = os.path.dirname(sys.executable)
                os.add_dll_directory(app_path)
                
                # Ajouter les sous-dossiers libs et ryzenadj
                for subdir in ['libs', 'ryzenadj']:
                    subdir_path = os.path.join(app_path, subdir)
                    if os.path.exists(subdir_path):
                        os.add_dll_directory(subdir_path)

    except Exception as e:
        print(f"Warning: Could not add DLL directories: {e}")

def setup_environment():
    # Configurer l'environnement pour les DLLs
    add_dll_directory()
    
    # Configurer pkg_resources
    if getattr(sys, 'frozen', False):
        import pkg_resources
        pkg_resources.working_set.add_entry(os.path.dirname(sys.executable))

setup_environment() 