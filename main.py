#!/usr/bin/env python3
"""
Framework Control Center - Main entry point
"""

import asyncio
import os
import sys
import traceback
from pathlib import Path
import ctypes
import win32con
import win32gui

from framework_cc.admin import is_admin, run_as_admin
from framework_cc.gui import FrameworkControlCenter
from framework_cc.logger import logger

def hide_console():
    """Hide console window."""
    try:
        # Get the console window by its window class name
        console_window = win32gui.FindWindow("ConsoleWindowClass", None)
        if console_window:
            # Only hide if it's actually a console window
            win32gui.ShowWindow(console_window, win32con.SW_HIDE)
            logger.debug("Console window hidden successfully")
    except Exception as e:
        logger.error(f"Failed to hide console: {e}")

def setup_environment():
    """Setup the application environment."""
    # Create necessary directories if they don't exist
    for directory in ["configs", "libs", "assets", "fonts"]:
        try:
            path = Path(directory)
            if not path.exists():
                path.mkdir(parents=True)
                logger.info(f"Created directory: {directory}")
            else:
                logger.debug(f"Directory already exists: {directory}")
        except Exception as e:
            logger.warning(f"Could not create directory {directory}: {e}")
            # Continue even if directory creation fails as it might already exist
            pass

def main():
    """Main entry point."""
    try:
        # Hide console window if running as exe
        if getattr(sys, 'frozen', False):
            hide_console()

        # Check for admin privileges
        if not is_admin():
            logger.info("Requesting administrator privileges...")
            try:
                ctypes.windll.shell32.ShellExecuteW(
                    None,
                    "runas",
                    sys.executable,
                    " ".join(sys.argv),
                    None,
                    1  # SW_SHOWNORMAL
                )
                sys.exit(0)
            except Exception as e:
                logger.error(f"Failed to obtain administrator privileges: {e}")
                sys.exit(1)

        # Setup environment
        setup_environment()
        
        # Create and run application
        logger.info("Starting Framework Control Center...")
        app = FrameworkControlCenter()
        
        # Run the application
        app.mainloop()
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main() 