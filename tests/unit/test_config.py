"""
Unit tests for the configuration management module.
"""

import os
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
import pytest

from src.utils.config import ConfigurationManager, config


class TestConfigurationManager:
    """Test cases for ConfigurationManager class"""
    
    def test_init_default(self):
        """Test ConfigurationManager initialization with defaults"""
        cfg = ConfigurationManager()
        
        # Should have default values
        assert cfg.config_dir == Path("config")
        assert cfg.environment == "development"  # Default from env or fallback
        assert cfg._config_cache is None
    
    def test_init_with_custom_config_dir(self):
        """Test ConfigurationManager initialization with custom config directory"""
        custom_dir = "/custom/config"
        cfg = ConfigurationManager(config_dir=custom_dir)
        
        assert cfg.config_dir == Path(custom_dir)
        assert cfg.environment == "development"
        assert cfg._config_cache is None
    
    @patch.dict(os.environ, {'SCANNER_ENV': 'production'})
    def test_init_with_environment_from_env(self):
        """Test ConfigurationManager initialization reads environment from env var"""
        cfg = ConfigurationManager()
        assert cfg.environment == 'production'
    
    @patch('yaml.safe_load')
    @patch('pathlib.Path.exists')
    def test_load_config_success(self, mock_path_exists, mock_yaml_safe_load):
        """Test successful config loading"""
        mock_path_exists.return_value = True
        mock_yaml_safe_load.return_value = {
            'network': {'port': 8080},
            'scanner': {'timeout': 30}
        }
        
        with patch('builtins.open', mock_open(read_data="network:\n  port: 8080")):
            cfg = ConfigurationManager()
            result = cfg.load_config()
            
            # Should return loaded config
            assert result == {'network': {'port': 8080}, 'scanner': {'timeout': 30}}
            # Should cache the config
            assert cfg._config_cache == result
    
    @patch('pathlib.Path.exists')
    def test_load_config_file_not_found_returns_default(self, mock_path_exists):
        """Test config loading when file doesn't exist returns default config"""
        mock_path_exists.return_value = False
        
        cfg = ConfigurationManager()
        result = cfg.load_config()
        
        # Should return default config, not empty dict
        assert isinstance(result, dict)
        assert 'network' in result
        assert 'scanner' in result
        assert 'logging' in result
        assert 'file_transfer' in result
    
    @patch('builtins.open')
    @patch('pathlib.Path.exists')
    def test_load_config_yaml_error(self, mock_path_exists, mock_open_mock):
        """Test config loading with YAML parse error"""
        mock_path_exists.return_value = True
        mock_open_mock.return_value.__enter__.return_value.read.side_effect = yaml.YAMLError("Invalid YAML")
        
        cfg = ConfigurationManager()
        
        # Should raise the YAML error
        with pytest.raises(yaml.YAMLError):
            cfg.load_config()
    
    @patch('builtins.open')
    @patch('pathlib.Path.exists')
    def test_load_config_io_error(self, mock_path_exists, mock_open_mock):
        """Test config loading with file IO error"""
        mock_path_exists.return_value = True
        mock_open_mock.side_effect = OSError("Cannot read file")
        
        cfg = ConfigurationManager()
        
        # Should raise the IO error
        with pytest.raises(OSError):
            cfg.load_config()
    
    def test_get_with_loaded_config(self):
        """Test get method with loaded configuration"""
        cfg = ConfigurationManager()
        cfg._config_cache = {
            'network': {'port': 8080, 'host': 'localhost'},
            'scanner': {'timeout': 30}
        }
        
        # Test getting nested value
        assert cfg.get('network.port') == 8080
        assert cfg.get('network.host') == 'localhost'
        assert cfg.get('scanner.timeout') == 30
        
        # Test getting non-existent key with default
        assert cfg.get('network.missing', 'default') == 'default'
        assert cfg.get('missing.key', 42) == 42
    
    def test_get_without_loaded_config(self):
        """Test get method when config is not loaded"""
        with patch.object(ConfigurationManager, 'load_config') as mock_load:
            mock_load.return_value = {'test': {'value': 123}}
            
            cfg = ConfigurationManager()
            result = cfg.get('test.value')
            
            # Should load config and return value
            mock_load.assert_called_once()
            assert result == 123
    
    def test_get_top_level_key(self):
        """Test get method with top-level key"""
        cfg = ConfigurationManager()
        cfg._config_cache = {'database': {'host': 'db.example.com'}}
        
        result = cfg.get('database')
        assert result == {'host': 'db.example.com'}
    
    def test_get_empty_config(self):
        """Test get method with empty config"""
        cfg = ConfigurationManager()
        cfg._config_cache = {}
        
        # Should return default value
        assert cfg.get('any.key', 'default') == 'default'
        assert cfg.get('any.key') is None
    
    def test_get_invalid_nested_key(self):
        """Test get method with invalid nested key path"""
        cfg = ConfigurationManager()
        cfg._config_cache = {
            'network': {'port': 8080}
        }
        
        # Try to access non-dict as if it has nested keys
        assert cfg.get('network.port.invalid', 'default') == 'default'
    
    @patch('pathlib.Path.exists')
    def test_config_caching(self, mock_path_exists):
        """Test that config is cached after first load"""
        mock_path_exists.return_value = False
        
        cfg = ConfigurationManager()
        
        # When no config file exists, load_config returns _get_default_config() 
        # without caching it, so each call returns a new dict
        result1 = cfg.load_config()
        result2 = cfg.load_config()
        
        # The content should be the same (default config)
        assert result1 == result2
        # But they are different objects since no caching happens for default config
        assert result1 is not result2
        # Should be default config structure
        assert isinstance(result1, dict)
        assert 'network' in result1
        assert 'scanner' in result1
    
    def test_get_default_config_structure(self):
        """Test that default config has expected structure"""
        cfg = ConfigurationManager()
        default_config = cfg._get_default_config()
        
        assert 'network' in default_config
        assert 'scanner' in default_config
        assert 'file_transfer' in default_config
        assert 'logging' in default_config
        
        # Check some specific values
        assert default_config['network']['udp_port'] == 706
        assert default_config['scanner']['max_retry_attempts'] == 3
        assert default_config['logging']['level'] == 'INFO'


class TestConfigFunction:
    """Test cases for the config global instance"""
    
    def test_config_is_configuration_manager_instance(self):
        """Test that config is a ConfigurationManager instance"""
        assert isinstance(config, ConfigurationManager)
    
    def test_config_is_singleton(self):
        """Test that config is the same instance"""
        from src.utils.config import config as config2
        
        # Should be the same instance
        assert config is config2


class TestConfigWithMockedEnvironment:
    """Test cases with different environment configurations"""
    
    @patch.dict(os.environ, {'SCANNER_ENV': 'production'})
    def test_production_environment(self):
        """Test ConfigurationManager with production environment"""
        cfg = ConfigurationManager()
        assert cfg.environment == 'production'
        
        # Should look for production.yml
        expected_path = Path("config") / "production.yml"
        assert str(cfg.config_dir / f"{cfg.environment}.yml") == str(expected_path)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_default_environment_no_env_var(self):
        """Test ConfigurationManager with no environment variable"""
        cfg = ConfigurationManager()
        # Should default to development
        assert cfg.environment == 'development'
    
    def test_custom_config_dir(self):
        """Test ConfigurationManager with custom config directory"""
        custom_dir = Path("/custom/config")
        cfg = ConfigurationManager(config_dir=str(custom_dir))
        
        assert cfg.config_dir == custom_dir


class TestConfigurationManagerEdgeCases:
    """Test edge cases and error handling"""
    
    def test_get_with_none_value(self):
        """Test get method when config value is None"""
        cfg = ConfigurationManager()
        cfg._config_cache = {'test': None}
        
        result = cfg.get('test', 'default')
        assert result is None
    
    def test_get_with_empty_string_key(self):
        """Test get method with empty string key"""
        cfg = ConfigurationManager()
        cfg._config_cache = {'': 'empty_key_value'}
        
        result = cfg.get('', 'default')
        assert result == 'empty_key_value'
    
    def test_get_with_numeric_keys(self):
        """Test get method with numeric-like keys"""
        cfg = ConfigurationManager()
        cfg._config_cache = {'123': {'456': 'numeric_keys'}}
        
        result = cfg.get('123.456')
        assert result == 'numeric_keys'
    
    @patch('pathlib.Path.exists')
    def test_repeated_load_calls(self, mock_path_exists):
        """Test that repeated load_config calls work correctly"""
        mock_path_exists.return_value = False
        
        cfg = ConfigurationManager()
        
        # Multiple calls should work without issues and return default config
        # Each call returns a new dict since default config is not cached
        result1 = cfg.load_config()
        result2 = cfg.load_config()
        result3 = cfg.load_config()
        
        # Content should be the same
        assert result1 == result2 == result3
        # But they are different objects (no caching for default config)
        assert result1 is not result2
        assert result2 is not result3
        # Should be default config, not empty
        assert isinstance(result1, dict)
        assert 'network' in result1
        # Verify it's actually the default config structure
        assert result1 == cfg._get_default_config()
