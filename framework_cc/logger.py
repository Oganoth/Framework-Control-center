"""Logging configuration for Framework Control Center."""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Optional

def setup_logger(name: str = "framework_cc", log_level: str = "INFO") -> logging.Logger:
    """Setup application logger with rotation and proper formatting.
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        logging.Logger: Configured logger instance
    """
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers to prevent duplicates
    logger.handlers.clear()
    
    # Create formatters
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    
    # Setup rotating file handler
    # Rotate at 5MB, keep 5 backups
    file_handler = logging.handlers.RotatingFileHandler(
        log_dir / "framework_cc.log",
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    return logger

def check_and_rotate_log(log_file: Optional[str] = None) -> None:
    """Check log file size and rotate if necessary.
    
    Args:
        log_file: Path to log file to check. If None, uses default log file.
    """
    if log_file is None:
        log_file = Path("logs/framework_cc.log")
    else:
        log_file = Path(log_file)
        
    try:
        if log_file.exists():
            size_mb = log_file.stat().st_size / (1024 * 1024)  # Convert to MB
            if size_mb >= 5:  # Rotate at 5MB
                # Create backup filename
                backup_num = 1
                while (backup_file := log_file.with_suffix(f'.log.{backup_num}')).exists():
                    backup_num += 1
                    if backup_num > 5:  # Keep max 5 backups
                        oldest_backup = log_file.with_suffix('.log.1')
                        oldest_backup.unlink(missing_ok=True)
                        # Rename existing backups
                        for i in range(1, 5):
                            current = log_file.with_suffix(f'.log.{i+1}')
                            if current.exists():
                                current.rename(log_file.with_suffix(f'.log.{i}'))
                        backup_num = 5
                
                # Rotate log file
                log_file.rename(backup_file)
                
                # Create new empty log file
                log_file.touch()
                logger.info(f"Rotated log file to {backup_file}")
    except Exception as e:
        logger.error(f"Error rotating log file: {e}")

# Initialize logger
logger = setup_logger() 