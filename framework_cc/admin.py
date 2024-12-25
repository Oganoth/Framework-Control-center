import os
import sys
import ctypes
import win32com.shell.shell as shell
from pathlib import Path

def is_admin() -> bool:
    """Check if the current process has admin privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def run_as_admin():
    """Restart the current script with admin privileges."""
    if is_admin():
        return True

    script = Path(sys.argv[0]).resolve()
    params = ' '.join(sys.argv[1:])
    
    try:
        # Use ShellExecuteEx to run as admin
        ret = shell.ShellExecuteEx(
            lpVerb='runas',
            lpFile=sys.executable,
            lpParameters=f'"{script}" {params}',
            nShow=1
        )
        if int(ret['hInstApp']) > 32:
            return True
    except Exception as e:
        print(f"Error elevating privileges: {e}")
    return False 