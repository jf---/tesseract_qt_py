"""Cartesian position/orientation editor widget."""
from __future__ import annotations

from math import pi

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QDoubleSpinBox,
)


class CartesianEditorWidget(QWidget):
    """Widget for editing cartesian position and orientation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)

        # Position GroupBox
        position_group = QGroupBox("Position")
        position_group.setCheckable(True)
        position_group.setChecked(True)
        position_layout = QGridLayout(position_group)

        # X
        position_layout.addWidget(QLabel("X:"), 0, 0)
        self.x_spin = QDoubleSpinBox()
        self.x_spin.setRange(-100.0, 100.0)
        self.x_spin.setDecimals(6)
        self.x_spin.setSingleStep(0.001)
        position_layout.addWidget(self.x_spin, 0, 1)

        # Y
        position_layout.addWidget(QLabel("Y:"), 0, 2)
        self.y_spin = QDoubleSpinBox()
        self.y_spin.setRange(-100.0, 100.0)
        self.y_spin.setDecimals(6)
        self.y_spin.setSingleStep(0.001)
        position_layout.addWidget(self.y_spin, 0, 3)

        # Z
        position_layout.addWidget(QLabel("Z:"), 0, 4)
        self.z_spin = QDoubleSpinBox()
        self.z_spin.setRange(-100.0, 100.0)
        self.z_spin.setDecimals(6)
        self.z_spin.setSingleStep(0.001)
        position_layout.addWidget(self.z_spin, 0, 5)

        layout.addWidget(position_group)

        # Orientation GroupBox
        orientation_group = QGroupBox("Orientation")
        orientation_group.setCheckable(True)
        orientation_group.setChecked(True)
        orientation_layout = QVBoxLayout(orientation_group)

        # RPY section
        rpy_layout = QHBoxLayout()

        # Roll
        rpy_layout.addWidget(QLabel("Roll:"))
        self.roll_spin = QDoubleSpinBox()
        self.roll_spin.setRange(-pi, pi)
        self.roll_spin.setDecimals(6)
        self.roll_spin.setSingleStep(0.001)
        rpy_layout.addWidget(self.roll_spin)

        # Pitch
        rpy_layout.addWidget(QLabel("Pitch:"))
        self.pitch_spin = QDoubleSpinBox()
        self.pitch_spin.setRange(-pi / 2, pi / 2)
        self.pitch_spin.setDecimals(6)
        self.pitch_spin.setSingleStep(0.001)
        rpy_layout.addWidget(self.pitch_spin)

        # Yaw
        rpy_layout.addWidget(QLabel("Yaw:"))
        self.yaw_spin = QDoubleSpinBox()
        self.yaw_spin.setRange(-pi, pi)
        self.yaw_spin.setDecimals(6)
        self.yaw_spin.setSingleStep(0.001)
        rpy_layout.addWidget(self.yaw_spin)

        orientation_layout.addLayout(rpy_layout)

        # Quaternion section
        quat_layout = QHBoxLayout()

        # Quat X
        quat_layout.addWidget(QLabel("X:"))
        self.quat_x_spin = QDoubleSpinBox()
        self.quat_x_spin.setRange(-1.0, 1.0)
        self.quat_x_spin.setDecimals(6)
        self.quat_x_spin.setSingleStep(0.001)
        quat_layout.addWidget(self.quat_x_spin)

        # Quat Y
        quat_layout.addWidget(QLabel("Y:"))
        self.quat_y_spin = QDoubleSpinBox()
        self.quat_y_spin.setRange(-1.0, 1.0)
        self.quat_y_spin.setDecimals(6)
        self.quat_y_spin.setSingleStep(0.001)
        quat_layout.addWidget(self.quat_y_spin)

        # Quat Z
        quat_layout.addWidget(QLabel("Z:"))
        self.quat_z_spin = QDoubleSpinBox()
        self.quat_z_spin.setRange(-1.0, 1.0)
        self.quat_z_spin.setDecimals(6)
        self.quat_z_spin.setSingleStep(0.001)
        quat_layout.addWidget(self.quat_z_spin)

        # Quat W
        quat_layout.addWidget(QLabel("W:"))
        self.quat_w_spin = QDoubleSpinBox()
        self.quat_w_spin.setRange(-1.0, 1.0)
        self.quat_w_spin.setDecimals(6)
        self.quat_w_spin.setSingleStep(0.001)
        self.quat_w_spin.setValue(1.0)
        quat_layout.addWidget(self.quat_w_spin)

        orientation_layout.addLayout(quat_layout)

        layout.addWidget(orientation_group)
