"""Configuration management for Agent Stamina.

Supports TOML configuration files at ~/.agent-stamina/config.toml
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, Any


@dataclass
class StaminaConfig:
    """Configuration for Agent Stamina."""
    
    # Database settings
    db_path: str = ".agent_stamina.db"
    data_retention_days: int = 30
    
    # Monitoring settings
    snapshot_interval_minutes: int = 5
    system_health_interval_minutes: int = 10
    
    # Alert thresholds
    ram_warning_threshold: float = 75.0
    ram_critical_threshold: float = 90.0
    disk_warning_threshold: float = 85.0
    disk_critical_threshold: float = 95.0
    browser_warning_threshold: float = 800.0
    browser_critical_threshold: float = 1500.0
    
    # Prometheus exporter settings
    prometheus_enabled: bool = False
    prometheus_port: int = 9090
    
    # Logging settings
    log_level: str = "INFO"
    log_format: str = "text"  # or "json"
    log_file: Optional[str] = None
    
    # Dashboard settings
    dashboard_port: int = 8080
    dashboard_auto_refresh: bool = True
    dashboard_refresh_seconds: int = 30
    
    @classmethod
    def from_file(cls, path: Optional[str] = None) -> "StaminaConfig":
        """Load configuration from file."""
        if path is None:
            path = cls._default_config_path()
        
        if not os.path.exists(path):
            return cls()  # Return defaults
        
        try:
            # Try TOML first
            import tomllib
            with open(path, 'rb') as f:
                data = tomllib.load(f)
        except ImportError:
            try:
                # Fallback to tomli
                import tomli
                with open(path, 'rb') as f:
                    data = tomli.load(f)
            except ImportError:
                # Fallback to JSON
                try:
                    with open(path) as f:
                        data = json.load(f)
                except:
                    return cls()
        except Exception:
            return cls()
        
        # Filter to only known fields
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in known_fields}
        
        return cls(**filtered_data)
    
    @classmethod
    def from_env(cls) -> "StaminaConfig":
        """Load configuration from environment variables."""
        config = cls()
        
        # Map env vars to config fields
        env_mapping = {
            'AGENT_STAMINA_DB_PATH': 'db_path',
            'AGENT_STAMINA_RETENTION_DAYS': ('data_retention_days', int),
            'AGENT_STAMINA_SNAPSHOT_INTERVAL': ('snapshot_interval_minutes', int),
            'AGENT_STAMINA_PROMETHEUS_PORT': ('prometheus_port', int),
            'AGENT_STAMINA_PROMETHEUS_ENABLED': ('prometheus_enabled', lambda x: x.lower() == 'true'),
            'AGENT_STAMINA_LOG_LEVEL': 'log_level',
            'AGENT_STAMINA_LOG_FORMAT': 'log_format',
            'AGENT_STAMINA_LOG_FILE': 'log_file',
            'AGENT_STAMINA_DASHBOARD_PORT': ('dashboard_port', int),
        }
        
        for env_var, field_name in env_mapping.items():
            value = os.environ.get(env_var)
            if value:
                if isinstance(field_name, tuple):
                    name, converter = field_name
                    try:
                        setattr(config, name, converter(value))
                    except:
                        pass
                else:
                    setattr(config, field_name, value)
        
        return config
    
    @classmethod
    def load(cls, path: Optional[str] = None) -> "StaminaConfig":
        """Load configuration with priority: env vars > file > defaults."""
        # Start with defaults
        config = cls()
        
        # Override with file settings
        file_config = cls.from_file(path)
        for field_name in cls.__dataclass_fields__:
            file_value = getattr(file_config, field_name)
            default_value = getattr(cls(), field_name)
            if file_value != default_value:
                setattr(config, field_name, file_value)
        
        # Override with env vars (highest priority)
        env_config = cls.from_env()
        for field_name in cls.__dataclass_fields__:
            env_value = getattr(env_config, field_name)
            default_value = getattr(cls(), field_name)
            if env_value != default_value:
                setattr(config, field_name, env_value)
        
        return config
    
    def save(self, path: Optional[str] = None):
        """Save configuration to file."""
        if path is None:
            path = self._default_config_path()
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        try:
            # Try TOML
            import tomli_w
            with open(path, 'wb') as f:
                tomli_w.dump(asdict(self), f)
        except ImportError:
            # Fallback to JSON
            with open(path, 'w') as f:
                json.dump(asdict(self), f, indent=2)
    
    @staticmethod
    def _default_config_path() -> str:
        """Get default configuration file path."""
        return os.path.expanduser("~/.agent-stamina/config.toml")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


def get_config(path: Optional[str] = None) -> StaminaConfig:
    """Get the global configuration instance."""
    return StaminaConfig.load(path)


# Example config file content
EXAMPLE_CONFIG = '''# Agent Stamina Configuration
# Place at ~/.agent-stamina/config.toml

# Database settings
db_path = ".agent_stamina.db"
data_retention_days = 30

# Monitoring intervals
snapshot_interval_minutes = 5
system_health_interval_minutes = 10

# Alert thresholds
ram_warning_threshold = 75.0
ram_critical_threshold = 90.0
disk_warning_threshold = 85.0
disk_critical_threshold = 95.0
browser_warning_threshold = 800.0
browser_critical_threshold = 1500.0

# Prometheus exporter
prometheus_enabled = false
prometheus_port = 9090

# Logging
log_level = "INFO"
log_format = "text"  # or "json"
# log_file = "/var/log/agent-stamina.log"

# Dashboard
dashboard_port = 8080
dashboard_auto_refresh = true
dashboard_refresh_seconds = 30
'''


if __name__ == "__main__":
    # Demo
    print("=" * 60)
    print("Agent Stamina Configuration")
    print("=" * 60)
    
    config = get_config()
    
    print(f"\n📁 Config file: {config._default_config_path()}")
    print(f"📊 Database: {config.db_path}")
    print(f"🔄 Snapshot interval: {config.snapshot_interval_minutes} min")
    print(f"🌐 Prometheus: {'enabled' if config.prometheus_enabled else 'disabled'} (port {config.prometheus_port})")
    print(f"📈 Dashboard: port {config.dashboard_port}")
    print(f"📝 Log level: {config.log_level} ({config.log_format} format)")
    
    print("\n" + "=" * 60)
    print("Example config file:")
    print("=" * 60)
    print(EXAMPLE_CONFIG)
