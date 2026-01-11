"""Contact visualization example."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from tesseract_robotics.tesseract_collision import (
    ContactRequest,
    ContactResultMap,
    ContactResultVector,
    ContactTestType_ALL,
)
from tesseract_robotics.tesseract_common import (
    CollisionMarginData,
    FilesystemPath,
    GeneralResourceLocator,
)

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from tesseract_robotics.tesseract_environment import Environment

from widgets.render_widget import RenderWidget


class ContactDemoWindow(QMainWindow):
    """Demo window for contact visualization."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Contact Visualization Demo")
        self.resize(1200, 800)
        self._env = None
        self._setup_ui()

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        self.render = RenderWidget()
        layout.addWidget(self.render)

        # Buttons
        btn_check = QPushButton("Check Collisions")
        btn_check.clicked.connect(self._check_collisions)
        layout.addWidget(btn_check)

        btn_clear = QPushButton("Clear Contacts")
        btn_clear.clicked.connect(self._clear_contacts)
        layout.addWidget(btn_clear)

    def load_environment(self, urdf_path: str, srdf_path: str = None):
        """Load robot environment."""
        self._env = Environment()
        loc = GeneralResourceLocator()

        if not self._env.init(
            FilesystemPath(urdf_path),
            FilesystemPath(srdf_path) if srdf_path else FilesystemPath(),
            loc,
        ):
            raise RuntimeError("Failed to init environment")

        self.render.load_environment(self._env)

    def _check_collisions(self):
        """Run collision check and visualize."""
        if not self._env:
            return

        # Get discrete contact manager
        manager = self._env.getDiscreteContactManager()
        manager.setActiveCollisionObjects(self._env.getActiveLinkNames())

        # Set margin
        margin = CollisionMarginData(0.0)
        manager.setCollisionMarginData(margin)

        # Update transforms
        state = self._env.getState()
        manager.setCollisionObjectsTransform(state.link_transforms)

        # Execute check
        result_map = ContactResultMap()
        manager.contactTest(result_map, ContactRequest(ContactTestType_ALL))

        # Flatten results
        results = ContactResultVector()
        result_map.flattenMoveResults(results)

        print(f"Found {len(results)} contacts")
        for i, contact in enumerate(results):
            print(
                f"Contact {i}: {contact.link_names[0]} <-> {contact.link_names[1]}, dist={contact.distance:.4f}"
            )

        # Visualize
        self.render.scene.visualize_contacts(results)
        self.render.render()

    def _clear_contacts(self):
        """Clear contact visualization."""
        self.render.scene.clear_contacts()
        self.render.render()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = ContactDemoWindow()
    window.show()

    # Load example robot if path provided
    if len(sys.argv) > 1:
        urdf = sys.argv[1]
        srdf = sys.argv[2] if len(sys.argv) > 2 else None
        window.load_environment(urdf, srdf)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
