import json
from typing import Dict, Any
from pathlib import Path
from sc_tui.config import get_config_file

class Settings:
    def __init__(self):
        self.config_path = get_config_file()
        self._data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=4)
        except Exception as e:
            print(f"Failed to save config: {e}")

    @property
    def auth_method(self) -> str:
        """'browser' or 'file' or 'none'"""
        return self._data.get("auth_method", "none")

    @auth_method.setter
    def auth_method(self, value: str):
        self._data["auth_method"] = value
        self._save()

    @property
    def auth_browser(self) -> str:
        """'chrome', 'firefox', etc."""
        return self._data.get("auth_browser", "chrome")

    @auth_browser.setter
    def auth_browser(self, value: str):
        self._data["auth_browser"] = value
        self._save()

    @property
    def auth_cookie_file(self) -> str:
        return self._data.get("auth_cookie_file", "")

    @auth_cookie_file.setter
    def auth_cookie_file(self, value: str):
        self._data["auth_cookie_file"] = value
        self._save()

settings = Settings()
