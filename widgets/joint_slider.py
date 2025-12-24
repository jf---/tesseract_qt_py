"""Joint state slider widget."""
from __future__ import annotations

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QSlider,
    QLabel,
    QDoubleSpinBox,
    QFrame,
    QGroupBox,
    QPushButton,
)


class JointSlider(QFrame):
    """Single joint slider with label and spinbox."""

    valueChanged = Signal(str, float)  # joint_name, value

    def __init__(self, name: str, lower: float, upper: float, value: float = 0.0, parent=None):
        super().__init__(parent)
        self.name = name
        self.lower = lower
        self.upper = upper
        self._value = value
        self._updating = False

        self._setup_ui()
        self.set_value(value)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(8)

        # Joint name label
        self.label = QLabel(self.name)
        self.label.setFixedWidth(120)
        self.label.setToolTip(f"{self.name}\nRange: [{self.lower:.3f}, {self.upper:.3f}]")
        layout.addWidget(self.label)

        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 1000)
        self.slider.valueChanged.connect(self._on_slider_changed)
        layout.addWidget(self.slider, stretch=1)

        # Spinbox
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setRange(self.lower, self.upper)
        self.spinbox.setDecimals(4)
        self.spinbox.setSingleStep(0.01)
        self.spinbox.setFixedWidth(90)
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)
        layout.addWidget(self.spinbox)

    def _on_slider_changed(self, value: int):
        if self._updating:
            return
        self._updating = True

        # Convert slider to actual value
        t = value / 1000.0
        actual = self.lower + t * (self.upper - self.lower)
        self._value = actual
        self.spinbox.setValue(actual)
        self.valueChanged.emit(self.name, actual)

        self._updating = False

    def _on_spinbox_changed(self, value: float):
        if self._updating:
            return
        self._updating = True

        self._value = value
        # Convert actual value to slider position
        if self.upper > self.lower:
            t = (value - self.lower) / (self.upper - self.lower)
            self.slider.setValue(int(t * 1000))
        self.valueChanged.emit(self.name, value)

        self._updating = False

    def set_value(self, value: float):
        """Set joint value."""
        self._updating = True
        self._value = max(self.lower, min(self.upper, value))
        self.spinbox.setValue(self._value)
        if self.upper > self.lower:
            t = (self._value - self.lower) / (self.upper - self.lower)
            self.slider.setValue(int(t * 1000))
        self._updating = False

    def value(self) -> float:
        return self._value


class JointSliderWidget(QWidget):
    """Widget containing sliders for all joints."""

    jointValueChanged = Signal(str, float)  # joint_name, value
    jointValuesChanged = Signal(dict)  # all joint values

    def __init__(self, parent=None):
        super().__init__(parent)
        self.sliders: dict[str, JointSlider] = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header with buttons
        header = QHBoxLayout()

        self.btn_zero = QPushButton("Zero All")
        self.btn_zero.clicked.connect(self._on_zero_all)
        header.addWidget(self.btn_zero)

        self.btn_random = QPushButton("Random")
        self.btn_random.clicked.connect(self._on_random)
        header.addWidget(self.btn_random)

        header.addStretch()
        layout.addLayout(header)

        # Scroll area for sliders
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.slider_container = QWidget()
        self.slider_layout = QVBoxLayout(self.slider_container)
        self.slider_layout.setContentsMargins(0, 0, 0, 0)
        self.slider_layout.setSpacing(2)
        self.slider_layout.addStretch()

        scroll.setWidget(self.slider_container)
        layout.addWidget(scroll)

    def set_joints(self, joints: dict[str, tuple[float, float, float]]):
        """Setup sliders for joints.

        Args:
            joints: Dict mapping joint name to (lower, upper, current) limits
        """
        # Clear existing
        for slider in self.sliders.values():
            slider.deleteLater()
        self.sliders.clear()

        # Remove stretch
        while self.slider_layout.count():
            item = self.slider_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add new sliders
        for name, (lower, upper, value) in joints.items():
            slider = JointSlider(name, lower, upper, value)
            slider.valueChanged.connect(self._on_joint_changed)
            self.sliders[name] = slider
            self.slider_layout.addWidget(slider)

        self.slider_layout.addStretch()

    def set_joint_groups(self, groups: dict[str, dict[str, tuple[float, float, float]]]):
        """Setup sliders organized by groups.

        Args:
            groups: Dict mapping group name to joints dict
        """
        # Clear existing
        for slider in self.sliders.values():
            slider.deleteLater()
        self.sliders.clear()

        while self.slider_layout.count():
            item = self.slider_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add groups
        for group_name, joints in groups.items():
            group = QGroupBox(group_name)
            group.setCheckable(True)
            group.setChecked(True)
            group_layout = QVBoxLayout(group)
            group_layout.setContentsMargins(4, 4, 4, 4)
            group_layout.setSpacing(2)

            for name, (lower, upper, value) in joints.items():
                slider = JointSlider(name, lower, upper, value)
                slider.valueChanged.connect(self._on_joint_changed)
                self.sliders[name] = slider
                group_layout.addWidget(slider)

            self.slider_layout.addWidget(group)

        self.slider_layout.addStretch()

    def _on_joint_changed(self, name: str, value: float):
        """Handle single joint change."""
        self.jointValueChanged.emit(name, value)
        self.jointValuesChanged.emit(self.get_values())

    def get_values(self) -> dict[str, float]:
        """Get all joint values."""
        return {name: slider.value() for name, slider in self.sliders.items()}

    def set_values(self, values: dict[str, float]):
        """Set multiple joint values."""
        for name, value in values.items():
            if name in self.sliders:
                self.sliders[name].set_value(value)
        self.jointValuesChanged.emit(self.get_values())

    def _on_zero_all(self):
        """Set all joints to zero."""
        for slider in self.sliders.values():
            slider.set_value(0.0)
        self.jointValuesChanged.emit(self.get_values())

    def _on_random(self):
        """Set random joint values."""
        import random

        for slider in self.sliders.values():
            value = random.uniform(slider.lower, slider.upper)
            slider.set_value(value)
        self.jointValuesChanged.emit(self.get_values())
