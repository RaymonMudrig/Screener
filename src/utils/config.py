"""
Configuration management for stock screener
Loads and provides access to settings from YAML config file
"""

import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """Configuration manager"""

    _instance = None
    _config = None

    def __new__(cls, *args, **kwargs):
        """Singleton pattern to ensure single config instance"""
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_path: str = None):
        """Initialize configuration"""
        if self._config is None:
            if config_path is None:
                # Default config path
                config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
            self.load_config(config_path)

    def load_config(self, config_path: str) -> None:
        """Load configuration from YAML file"""
        config_file = Path(config_path)

        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        with open(config_file, 'r') as f:
            self._config = yaml.safe_load(f)

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation
        Example: config.get('database.path')
        """
        if self._config is None:
            raise ValueError("Configuration not loaded")

        keys = key_path.split('.')
        value = self._config

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default

        return value

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self.get(section, {})

    @property
    def database(self) -> Dict[str, Any]:
        """Get database configuration"""
        return self.get_section('database')

    @property
    def data_sources(self) -> Dict[str, Any]:
        """Get data sources configuration"""
        return self.get_section('data_sources')

    @property
    def indicators(self) -> Dict[str, Any]:
        """Get indicators configuration"""
        return self.get_section('indicators')

    @property
    def signals(self) -> Dict[str, Any]:
        """Get signals configuration"""
        return self.get_section('signals')

    @property
    def fetching(self) -> Dict[str, Any]:
        """Get fetching configuration"""
        return self.get_section('fetching')

    @property
    def scheduling(self) -> Dict[str, Any]:
        """Get scheduling configuration"""
        return self.get_section('scheduling')

    @property
    def logging(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return self.get_section('logging')

    @property
    def performance(self) -> Dict[str, Any]:
        """Get performance configuration"""
        return self.get_section('performance')

    def update(self, key_path: str, value: Any) -> None:
        """
        Update configuration value
        Example: config.update('database.path', '/new/path')
        """
        keys = key_path.split('.')
        config = self._config

        # Navigate to the parent of the target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]

        # Set the value
        config[keys[-1]] = value

    def save(self, config_path: str = None) -> None:
        """Save current configuration to file"""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"

        with open(config_path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False, sort_keys=False)


# Global config instance
_global_config = None


def get_config(config_path: str = None) -> Config:
    """Get global configuration instance"""
    global _global_config
    if _global_config is None:
        _global_config = Config(config_path)
    return _global_config


# Convenience functions
def get_db_path() -> str:
    """Get database path from config"""
    return get_config().get('database.path', 'database/stockCode.sqlite')


def get_stock_list_url() -> str:
    """Get stock list URL from config"""
    return get_config().get('data_sources.stock_list_url')


def get_price_data_url() -> str:
    """Get price data URL from config"""
    return get_config().get('data_sources.price_data_url')


def get_verify_ssl() -> bool:
    """Get SSL verification setting"""
    return get_config().get('data_sources.verify_ssl', False)


def get_retry_attempts() -> int:
    """Get retry attempts setting"""
    return get_config().get('data_sources.retry_attempts', 3)
