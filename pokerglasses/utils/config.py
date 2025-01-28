"""
Configuration handling module.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

class Config:
    """Configuration manager for PokerGlasses."""
    
    def __init__(self):
        self.config_dir = Path("config")
        self.default_config = self.config_dir / "default.yml"
        self.user_config = self.config_dir / "user.yml"
        self._config: Dict[str, Any] = {}
        self.load_config()

    def load_config(self) -> None:
        """Load configuration from files."""
        # Load default config
        if self.default_config.exists():
            with open(self.default_config, 'r') as f:
                self._config.update(yaml.safe_load(f))

        # Load and merge user config
        if self.user_config.exists():
            with open(self.user_config, 'r') as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    self._config.update(user_config)

    def save_user_config(self) -> None:
        """Save current configuration to user config file."""
        self.config_dir.mkdir(exist_ok=True)
        with open(self.user_config, 'w') as f:
            yaml.dump(self._config, f)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        self._config[key] = value

    def create_default_config(self) -> None:
        """Create default configuration file if it doesn't exist."""
        if not self.default_config.exists():
            default_settings = {
                'camera': {
                    'device_id': 0,
                    'resolution': {
                        'width': 1280,
                        'height': 720
                    }
                },
                'display': {
                    'brightness': 0.8,
                    'default_mode': 'basic'
                },
                'ml': {
                    'model_path': 'models/card_detection.pt',
                    'confidence_threshold': 0.85
                },
                'game': {
                    'auto_detect': True,
                    'calculation_delay': 0.5
                }
            }
            
            self.config_dir.mkdir(exist_ok=True)
            with open(self.default_config, 'w') as f:
                yaml.dump(default_settings, f)
            self._config.update(default_settings)

# Global configuration instance
config = Config() 