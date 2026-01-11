#!/usr/bin/env python3
"""Test coordinate frame visualization."""

from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app import TesseractViewer


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    viewer = TesseractViewer()
    viewer.show()

    # Load a URDF if provided
    if len(sys.argv) > 1:
        urdf_path = sys.argv[1]
        srdf_path = sys.argv[2] if len(sys.argv) > 2 else None
        viewer.load(urdf_path, srdf_path)

        # Demo: show frames for all links
        print("\nCoordinate frame controls:")
        print("- Toolbar: 'Frames' button toggles all link frames")
        print("- Toolbar: 'TCP' button toggles TCP frame (if set)")
        print("- Right-click link in tree -> 'Show Frame' / 'Hide Frame'")
        print("\nAPI usage:")
        print("  viewer.render.scene.show_frame('link_name', True)")
        print("  viewer.render.scene.set_frame_size(0.2)")
        print("  viewer.render.scene.set_tcp_link('tool0')")
        print("  viewer.render.scene.show_tcp_frame(True)")

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
