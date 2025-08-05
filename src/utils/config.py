"""
Configuration management system.
Follows SRP - Single responsibility for configuration.
"""
import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigurationManager:
    """Manages application configuration with environment-specific settings"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        # Check both SCANNER_ENV and SCANNER_CONFIG_ENV for environment setting
        self.environment = os.getenv("SCANNER_CONFIG_ENV") or os.getenv("SCANNER_ENV", "development")
        self._config_cache: Optional[Dict[str, Any]] = None
        self._runtime_overrides: Optional[Dict[str,Any]] = {
            'username' : os.getenv("USERNAME", "Shared")
        }
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration for the current environment"""
        if self._config_cache is not None:
            return self._config_cache
        
        config_file = self.config_dir / f"{self.environment}.yml"
        
        if not config_file.exists():
            # Fallback to development config
            config_file = self.config_dir / "development.yml"
        
        if not config_file.exists():
            # Return default configuration
            config_data = self._get_default_config()

        else:     
            try:
                with config_file.open('r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
            except (yaml.YAMLError, IOError) as e:
                # If config file is invalid, fall back to defaults
                config_data = self._get_default_config()
        
        #append runtime overrides to config
        config_data.setdefault("runtime",{}).update(self._runtime_overrides)
        self._config_cache = config_data
        
        return self._config_cache
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by key (supports dot notation)"""
        config = self.load_config()
        keys = key.split('.')
        
        current = config
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Default configuration if no config files exist"""
        return {
            "network": {
                "udp_port": 706,
                "tcp_port": 708,
                "discovery_timeout": 10.0,
                "socket_timeout": 1.0,
                "buffer_size": 1024,
                "tcp_chunk_size": 8192,
                "tcp_connection_timeout": 10.0
            },
            "scanner": {
                "default_src_name": "Scanner",
                "max_retry_attempts": 3,
                "default_file_path": "files/scan.raw",
                "files_directory": "files"
            },
            "file_transfer": {
                "handshake_message": "FILE_TRANSFER_READY",
                "size_ok_message": "SIZE_OK",
                "complete_message": "FILE_TRANSFER_COMPLETE",
                "transfer_ok_message": "TRANSFER_OK"
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file_enabled": True,
                "file_path": "logs/scanner.log",
                "max_file_size": 10485760,  # 10MB
                "backup_count": 5,
                "console_enabled": True
            }
        }


# Global configuration instance
config = ConfigurationManager()
