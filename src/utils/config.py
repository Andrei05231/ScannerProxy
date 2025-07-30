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
        self.environment = os.getenv("SCANNER_ENV", "development")
        self._config_cache: Optional[Dict[str, Any]] = None
    
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
            return self._get_default_config()
        
        with open(config_file, 'r') as f:
            self._config_cache = yaml.safe_load(f)
        
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
                "socket_timeout": 1.0
            },
            "scanner": {
                "default_src_name": "Scanner",
                "max_retry_attempts": 3
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }


# Global configuration instance
config = ConfigurationManager()
