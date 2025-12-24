"""State save/restore for joint configurations."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class StateManager:
    """Manages named joint configurations."""

    def __init__(self):
        self.poses: dict[str, dict[str, float]] = {}

    def save_pose(self, name: str, values: dict[str, float]):
        """Save named joint configuration."""
        self.poses[name] = values.copy()

    def load_pose(self, name: str) -> dict[str, float] | None:
        """Load named joint configuration."""
        return self.poses.get(name)

    def delete_pose(self, name: str):
        """Delete named configuration."""
        self.poses.pop(name, None)

    def list_poses(self) -> list[str]:
        """List all pose names."""
        return sorted(self.poses.keys())

    def save_to_file(self, path: Path | str):
        """Save all poses to JSON file."""
        path = Path(path)
        with path.open("w") as f:
            json.dump(self.poses, f, indent=2)

    def load_from_file(self, path: Path | str):
        """Load poses from JSON file."""
        path = Path(path)
        with path.open("r") as f:
            self.poses = json.load(f)

    def clear(self):
        """Clear all poses."""
        self.poses.clear()
