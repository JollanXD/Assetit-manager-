"""Safe, atomic persistence for user preferences outside the install directory."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def user_data_dir() -> Path:
    """Return the per-user data directory; portable app updates never overwrite it."""
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return base / "AssetIt"


class SettingsStore:
    """Small JSON settings store with defensive loading and atomic writes."""

    DEFAULTS: dict[str, Any] = {
        "schema_version": 1,
        "libraries": [],
        "favorites": [],
        "asset_tags": {},
        "thumbnail_size": 150,
        "ui_scale": 1.0,
        "language": "English",
    }

    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (user_data_dir() / "settings.json")

    def load(self) -> dict[str, Any]:
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(value, dict):
                value = {}
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            value = {}
        result = {**self.DEFAULTS, **value}
        result["libraries"] = self._string_list(result.get("libraries"))
        result["favorites"] = self._string_list(result.get("favorites"))
        if not isinstance(result.get("asset_tags"), dict):
            result["asset_tags"] = {}
        result["asset_tags"] = {
            str(key): self._string_list(tags)
            for key, tags in result["asset_tags"].items()
            if isinstance(tags, list)
        }
        try:
            result["thumbnail_size"] = max(64, min(512, int(result["thumbnail_size"])))
        except (TypeError, ValueError, OverflowError):
            result["thumbnail_size"] = self.DEFAULTS["thumbnail_size"]
        try:
            result["ui_scale"] = max(0.7, min(1.6, float(result["ui_scale"])))
        except (TypeError, ValueError, OverflowError):
            result["ui_scale"] = self.DEFAULTS["ui_scale"]
        return result

    def save(self, settings: dict[str, Any]) -> None:
        if not isinstance(settings, dict):
            raise TypeError("settings must be a dictionary")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(self.path.name + ".tmp")
        try:
            temporary.write_text(
                json.dumps(settings, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            temporary.replace(self.path)
        finally:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass

    @staticmethod
    def _string_list(value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if isinstance(item, (str, int, float))]
