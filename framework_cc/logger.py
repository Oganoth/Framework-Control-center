import logging
import sys
import os
from pathlib import Path
from datetime import datetime

def check_and_rotate_log(log_file: Path, max_size_mb: int = 10) -> Path:
    """Check log file size and rotate if needed.
    
    Args:
        log_file: Path to the log file
        max_size_mb: Maximum size in MB (default: 10)
        
    Returns:
        Path: Path to the current log file
    """
    try:
        if log_file.exists() and log_file.stat().st_size > max_size_mb * 1024 * 1024:
            # Rename existing log file with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_name = log_file.with_name(f"{log_file.stem}_{timestamp}{log_file.suffix}")
            log_file.rename(backup_name)
            
            # Create new log file
            log_file.touch()
            
            # Keep only last 5 backup files
            log_dir = log_file.parent
            backup_files = sorted(
                [f for f in log_dir.glob(f"{log_file.stem}_*{log_file.suffix}")],
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )
            for old_file in backup_files[4:]:  # Keep 5 most recent backups
                old_file.unlink()
    except Exception as e:
        print(f"Error rotating log file: {e}", file=sys.stderr)
    
    return log_file

def setup_logger(name: str = "framework_cc") -> logging.Logger:
    """Setup application logger with file and console output."""
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )

    # File handler - daily log file
    log_file = logs_dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
    log_file = check_and_rotate_log(log_file)  # Check size and rotate if needed
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# Create default logger
logger = setup_logger() 