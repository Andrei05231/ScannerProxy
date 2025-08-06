"""
Logging setup utility.
Configures file and console logging based on configuration settings.
"""
import logging
import logging.handlers
from pathlib import Path
import humanize
from .config import config


def setup_logging() -> None:
    """
    Setup logging based on configuration settings.
    Supports both file and console logging with rotation.
    """
    # Get logging configuration
    log_level = config.get('logging.level', 'INFO')
    log_format = config.get('logging.format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_enabled = config.get('logging.file_enabled', True)
    file_path = config.get('logging.file_path', 'logs/scanner.log')
    max_file_size = config.get('logging.max_file_size', 10485760)  # 10MB
    backup_count = config.get('logging.backup_count', 5)
    console_enabled = config.get('logging.console_enabled', True)
    
    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Create formatter
    formatter = logging.Formatter(log_format)
    
    # Get root logger and clear any existing handlers
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()
    
    # Setup file logging if enabled
    if file_enabled:
        # Ensure logs directory exists using pathlib
        log_file_path = Path(file_path)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=str(log_file_path),
            maxBytes=max_file_size,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        print(f"File logging enabled: {file_path} (max {max_file_size//1024//1024}MB, {backup_count} backups)")
    
    # Setup console logging if enabled
    if console_enabled:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        print(f"Console logging enabled: {log_level}")
    
    # Log the setup completion
    logger = logging.getLogger(__name__)
    logger.info("Logging system initialized")
    logger.info(f"Log level: {log_level}")
    logger.info(f"File logging: {'enabled' if file_enabled else 'disabled'}")
    logger.info(f"Console logging: {'enabled' if console_enabled else 'disabled'}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


def log_file_info() -> dict:
    """
    Get information about the current log file.
    
    Returns:
        Dictionary with log file information
    """
    file_path = Path(config.get('logging.file_path', 'logs/scanner.log'))
    
    if file_path.exists():
        stat = file_path.stat()
        return {
            'path': str(file_path),
            'size': stat.st_size,
            'size_mb': round(stat.st_size / 1024 / 1024, 2),
            'size_human': humanize.naturalsize(stat.st_size),
            'exists': True
        }
    else:
        return {
            'path': str(file_path),
            'size': 0,
            'size_mb': 0.0,
            'size_human': '0 B',
            'exists': False
        }
