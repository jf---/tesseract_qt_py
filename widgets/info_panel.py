"""Robot info panel widget."""
from __future__ import annotations

import numpy as np
from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QLabel,
)


def rotation_matrix_to_rpy(R: np.ndarray) -> tuple[float, float, float]:
    """Convert 3x3 rotation matrix to roll-pitch-yaw (XYZ Euler angles)."""
    sy = np.sqrt(R[0, 0]**2 + R[1, 0]**2)
    singular = sy < 1e-6

    if not singular:
        roll = np.arctan2(R[2, 1], R[2, 2])
        pitch = np.arctan2(-R[2, 0], sy)
        yaw = np.arctan2(R[1, 0], R[0, 0])
    else:
        roll = np.arctan2(-R[1, 2], R[1, 1])
        pitch = np.arctan2(-R[2, 0], sy)
        yaw = 0

    return roll, pitch, yaw


class RobotInfoPanel(QWidget):
    """Panel displaying robot state info."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._env = None
        self._joint_names = []
        self._joint_limits = {}
        self._tcp_link = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Robot info group
        info_group = QGroupBox("Robot Info")
        info_group.setCheckable(True)
        info_group.setChecked(True)
        info_layout = QVBoxLayout(info_group)

        self.name_label = QLabel("Name: -")
        self.dof_label = QLabel("DOF: 0")
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.dof_label)
        layout.addWidget(info_group)

        # Joint values table
        joint_group = QGroupBox("Joint Values")
        joint_group.setCheckable(True)
        joint_group.setChecked(True)
        joint_layout = QVBoxLayout(joint_group)

        self.joint_table = QTableWidget()
        self.joint_table.setColumnCount(4)
        self.joint_table.setHorizontalHeaderLabels(["Joint", "Value", "Min", "Max"])
        self.joint_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.joint_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.joint_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.joint_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.joint_table.setAlternatingRowColors(True)
        self.joint_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.joint_table.verticalHeader().setVisible(False)
        joint_layout.addWidget(self.joint_table)
        layout.addWidget(joint_group)

        # TCP pose group
        tcp_group = QGroupBox("TCP Pose")
        tcp_group.setCheckable(True)
        tcp_group.setChecked(True)
        tcp_layout = QVBoxLayout(tcp_group)

        self.tcp_xyz_label = QLabel("XYZ: -")
        self.tcp_rpy_label = QLabel("RPY: -")
        tcp_layout.addWidget(self.tcp_xyz_label)
        tcp_layout.addWidget(self.tcp_rpy_label)
        layout.addWidget(tcp_group)

        layout.addStretch()

    def load_environment(self, env, tcp_link: str | None = None):
        """Load environment and setup info display."""
        from tesseract_robotics.tesseract_scene_graph import JointType

        self._env = env
        self._tcp_link = tcp_link

        sg = env.getSceneGraph()

        # Get robot name (root link)
        root = sg.getRoot()
        self.name_label.setText(f"Name: {root}")

        # Get movable joints
        movable = (JointType.REVOLUTE, JointType.CONTINUOUS, JointType.PRISMATIC)
        self._joint_names = []
        self._joint_limits = {}

        for j in sg.getJoints():
            if j.type in movable:
                name = j.getName()
                self._joint_names.append(name)
                lim = j.limits
                if lim:
                    self._joint_limits[name] = (lim.lower, lim.upper)
                else:
                    self._joint_limits[name] = (-3.14, 3.14)

        self.dof_label.setText(f"DOF: {len(self._joint_names)}")

        # Setup joint table
        self.joint_table.setRowCount(len(self._joint_names))
        for i, name in enumerate(self._joint_names):
            # Joint name
            item = QTableWidgetItem(name)
            self.joint_table.setItem(i, 0, item)

            # Value (in degrees)
            item = QTableWidgetItem("0.0°")
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.joint_table.setItem(i, 1, item)

            # Limits (convert to degrees)
            lo, hi = self._joint_limits[name]
            item = QTableWidgetItem(f"{np.rad2deg(lo):.1f}°")
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.joint_table.setItem(i, 2, item)

            item = QTableWidgetItem(f"{np.rad2deg(hi):.1f}°")
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.joint_table.setItem(i, 3, item)

        # Update initial state
        self.update_state()

    def set_tcp_link(self, link_name: str | None):
        """Set TCP link for pose display."""
        self._tcp_link = link_name
        self.update_state()

    def update_joint_values(self, joint_values: dict[str, float]):
        """Update joint value display (input in radians, displayed in degrees)."""
        for i, name in enumerate(self._joint_names):
            if name in joint_values:
                value = joint_values[name]
                item = self.joint_table.item(i, 1)
                if item:
                    item.setText(f"{np.rad2deg(value):.1f}°")

        # Update TCP - set state first to ensure transforms are current
        if self._env:
            try:
                self._env.setState(joint_values)
            except Exception:
                pass
            self.update_state()

    def update_state(self):
        """Update TCP pose from environment state."""
        if not self._env:
            return

        try:
            state = self._env.getState()

            # Update TCP pose if link set
            if self._tcp_link and self._tcp_link in state.link_transforms:
                transform = state.link_transforms[self._tcp_link]
                matrix = transform.matrix()

                # Extract position
                x, y, z = matrix[0, 3], matrix[1, 3], matrix[2, 3]
                self.tcp_xyz_label.setText(f"XYZ: {x:.4f}, {y:.4f}, {z:.4f}")

                # Extract orientation (RPY)
                R = matrix[:3, :3]
                roll, pitch, yaw = rotation_matrix_to_rpy(R)
                self.tcp_rpy_label.setText(f"RPY: {roll:.4f}, {pitch:.4f}, {yaw:.4f}")
            else:
                self.tcp_xyz_label.setText("XYZ: -")
                self.tcp_rpy_label.setText("RPY: -")

        except Exception as e:
            logger.debug(f"Failed to update state: {e}")
