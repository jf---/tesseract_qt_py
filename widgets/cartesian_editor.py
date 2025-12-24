"""Cartesian position/orientation editor widget with sliders."""
from __future__ import annotations

from math import pi, degrees, radians

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QGroupBox,
    QLabel,
    QDoubleSpinBox,
    QSlider,
    QSizePolicy,
)
from PySide6.QtCore import Qt


class CartesianEditorWidget(QWidget):
    """Widget for editing cartesian position and orientation with sliders."""

    # Emitted when any value changes: (x, y, z, roll, pitch, yaw)
    poseChanged = Signal(float, float, float, float, float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._updating = False  # Prevent signal loops
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(3, 3, 3, 3)
        layout.setSpacing(6)

        # Position GroupBox
        position_group = QGroupBox("Position (m)")
        position_layout = QGridLayout(position_group)
        position_layout.setContentsMargins(6, 6, 6, 6)

        # X
        self.x_slider, self.x_spin = self._create_axis_control(
            position_layout, 0, "X", -2.0, 2.0, 0.0
        )

        # Y
        self.y_slider, self.y_spin = self._create_axis_control(
            position_layout, 1, "Y", -2.0, 2.0, 0.0
        )

        # Z
        self.z_slider, self.z_spin = self._create_axis_control(
            position_layout, 2, "Z", -2.0, 2.0, 0.5
        )

        layout.addWidget(position_group)

        # Orientation GroupBox (RPY in degrees)
        orientation_group = QGroupBox("Orientation (deg)")
        orientation_layout = QGridLayout(orientation_group)
        orientation_layout.setContentsMargins(6, 6, 6, 6)

        # Roll
        self.roll_slider, self.roll_spin = self._create_axis_control(
            orientation_layout, 0, "R", -180.0, 180.0, 0.0
        )

        # Pitch
        self.pitch_slider, self.pitch_spin = self._create_axis_control(
            orientation_layout, 1, "P", -90.0, 90.0, 0.0
        )

        # Yaw
        self.yaw_slider, self.yaw_spin = self._create_axis_control(
            orientation_layout, 2, "Y", -180.0, 180.0, 0.0
        )

        layout.addWidget(orientation_group)
        layout.addStretch()

    def _create_axis_control(
        self, layout: QGridLayout, row: int, label: str,
        min_val: float, max_val: float, default: float
    ) -> tuple[QSlider, QDoubleSpinBox]:
        """Create a slider + spinbox pair for an axis."""
        # Axis names for tooltips
        axis_names = {"X": "X position", "Y": "Y position", "Z": "Z position",
                      "R": "Roll (rotation about X)", "P": "Pitch (rotation about Y)",
                      "Y": "Yaw (rotation about Z)"}
        unit = "m" if label in ("X", "Y", "Z") else "deg"
        tooltip = f"{axis_names.get(label, label)}\nRange: [{min_val:.1f}, {max_val:.1f}] {unit}"

        # Label
        lbl = QLabel(f"{label}:")
        lbl.setFixedWidth(20)
        lbl.setToolTip(tooltip)
        layout.addWidget(lbl, row, 0)

        # Slider (integer, scaled by 1000 for precision)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(int(min_val * 1000), int(max_val * 1000))
        slider.setValue(int(default * 1000))
        slider.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        slider.setToolTip(tooltip)
        layout.addWidget(slider, row, 1)

        # Spinbox
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setDecimals(3)
        spin.setSingleStep(0.01 if abs(max_val) <= 10 else 1.0)
        spin.setValue(default)
        spin.setFixedWidth(80)
        spin.setToolTip(tooltip)
        layout.addWidget(spin, row, 2)

        # Connect slider <-> spinbox
        slider.valueChanged.connect(lambda v: self._on_slider_changed(spin, v))
        spin.valueChanged.connect(lambda v: self._on_spin_changed(slider, v))

        return slider, spin

    def _on_slider_changed(self, spin: QDoubleSpinBox, value: int):
        """Slider changed -> update spinbox."""
        if self._updating:
            return
        self._updating = True
        spin.setValue(value / 1000.0)
        self._updating = False
        self._emit_pose()

    def _on_spin_changed(self, slider: QSlider, value: float):
        """Spinbox changed -> update slider."""
        if self._updating:
            return
        self._updating = True
        slider.setValue(int(value * 1000))
        self._updating = False
        self._emit_pose()

    def _connect_signals(self):
        """Connect value change signals."""
        pass  # Already connected in _create_axis_control

    def _emit_pose(self):
        """Emit current pose values."""
        self.poseChanged.emit(
            self.x_spin.value(),
            self.y_spin.value(),
            self.z_spin.value(),
            radians(self.roll_spin.value()),
            radians(self.pitch_spin.value()),
            radians(self.yaw_spin.value()),
        )

    def set_pose(self, x: float, y: float, z: float, roll: float, pitch: float, yaw: float):
        """Set pose values (angles in radians)."""
        self._updating = True
        self.x_spin.setValue(x)
        self.y_spin.setValue(y)
        self.z_spin.setValue(z)
        self.roll_spin.setValue(degrees(roll))
        self.pitch_spin.setValue(degrees(pitch))
        self.yaw_spin.setValue(degrees(yaw))
        # Update sliders
        self.x_slider.setValue(int(x * 1000))
        self.y_slider.setValue(int(y * 1000))
        self.z_slider.setValue(int(z * 1000))
        self.roll_slider.setValue(int(degrees(roll) * 1000))
        self.pitch_slider.setValue(int(degrees(pitch) * 1000))
        self.yaw_slider.setValue(int(degrees(yaw) * 1000))
        self._updating = False

    def get_pose(self) -> tuple[float, float, float, float, float, float]:
        """Get current pose (x, y, z, roll, pitch, yaw) with angles in radians."""
        return (
            self.x_spin.value(),
            self.y_spin.value(),
            self.z_spin.value(),
            radians(self.roll_spin.value()),
            radians(self.pitch_spin.value()),
            radians(self.yaw_spin.value()),
        )

    def get_xyz(self) -> tuple[float, float, float]:
        """Get position only."""
        return (self.x_spin.value(), self.y_spin.value(), self.z_spin.value())

    def get_rpy_radians(self) -> tuple[float, float, float]:
        """Get orientation as RPY in radians."""
        return (
            radians(self.roll_spin.value()),
            radians(self.pitch_spin.value()),
            radians(self.yaw_spin.value()),
        )
