"""Demo of RobotInfoPanel widget."""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QSplitter

from tesseract_robotics.tesseract_environment import Environment
from tesseract_robotics.tesseract_common import GeneralResourceLocator, FilesystemPath
from tesseract_robotics.tesseract_scene_graph import JointType

sys.path.insert(0, str(Path(__file__).parent.parent))

from widgets.info_panel import RobotInfoPanel
from widgets.joint_slider import JointSliderWidget


class InfoPanelDemo(QMainWindow):
    """Demo window for info panel."""

    def __init__(self, urdf_path: str):
        super().__init__()
        self.setWindowTitle("Robot Info Panel Demo")
        self.resize(900, 700)

        # Load environment
        self.env = Environment()
        loc = GeneralResourceLocator()
        if not self.env.init(FilesystemPath(urdf_path), FilesystemPath(), loc):
            raise RuntimeError("Failed to load URDF")

        # Create widgets
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.joints = JointSliderWidget()
        self.info = RobotInfoPanel()

        splitter.addWidget(self.joints)
        splitter.addWidget(self.info)
        splitter.setSizes([400, 500])

        self.setCentralWidget(splitter)

        # Setup joints
        sg = self.env.getSceneGraph()
        movable = (JointType.REVOLUTE, JointType.CONTINUOUS, JointType.PRISMATIC)
        joints = {}
        tcp_link = None

        for j in sg.getJoints():
            if j.type in movable:
                lim = j.limits
                lo, hi = (lim.lower, lim.upper) if lim else (-3.14, 3.14)
                joints[j.getName()] = (lo, hi, 0.0)
                tcp_link = j.child_link_name  # Use last link as TCP

        self.joints.set_joints(joints)
        self.info.load_environment(self.env, tcp_link)

        # Connect signals
        self.joints.jointValuesChanged.connect(self._on_joints_changed)

    def _on_joints_changed(self, values: dict[str, float]):
        """Update environment and info panel."""
        for name, value in values.items():
            try:
                self.env.setState([name], [value])
            except Exception:
                pass
        self.info.update_state()


def main():
    if len(sys.argv) < 2:
        print("Usage: python info_panel_demo.py <urdf_file>")
        sys.exit(1)

    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    demo = InfoPanelDemo(sys.argv[1])
    demo.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
