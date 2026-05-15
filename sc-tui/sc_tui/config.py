import os
from pathlib import Path
from platformdirs import user_config_dir, user_cache_dir

APP_NAME = "sc-tui"
APP_AUTHOR = "sc-tui"

def get_config_dir() -> Path:
    """Returns the XDG-compliant config directory for the application."""
    path = Path(user_config_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_cache_dir() -> Path:
    """Returns the XDG-compliant cache directory for the application."""
    path = Path(user_cache_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_config_file() -> Path:
    """Returns the path to the main configuration file."""
    return get_config_dir() / "config.json"

def get_cache_db() -> Path:
    """Returns the path to the local cache DB."""
    return get_cache_dir() / "cache.json"
