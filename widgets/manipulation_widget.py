"""Manipulation widget for robot control."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QFormLayout,
    QTabWidget,
    QLabel,
    QComboBox,
    QPushButton,
    QFrame,
    QSpacerItem,
    QSizePolicy,
)

try:
    from tesseract_qt_py.widgets.joint_slider import JointSliderWidget
except ImportError:
    JointSliderWidget = None


class ManipulationWidget(QWidget):
    """Widget for robot manipulation control with multiple modes."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._setup_ui()

    def _setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(3, 3, 3, 3)

        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setCurrentIndex(0)
        main_layout.addWidget(self.tab_widget)

        # Create tabs
        self._create_config_tab()
        self._create_joint_tab()
        self._create_cartesian_tab()
        self._create_state_tab()

    def _create_config_tab(self):
        """Create configuration tab with combo boxes."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Frame with form layout
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.NoFrame)
        frame.setFrameShadow(QFrame.Shadow.Raised)

        form_layout = QFormLayout(frame)
        form_layout.setContentsMargins(0, 0, 0, 0)

        # Mode
        self.mode_combo_box = QComboBox()
        self.mode_combo_box.addItems(["Joint", "Cartesian"])
        form_layout.addRow(QLabel("Mode:"), self.mode_combo_box)

        # Group Name
        self.group_combo_box = QComboBox()
        form_layout.addRow(QLabel("Group Name:"), self.group_combo_box)

        # Working Frame
        self.working_frame_combo_box = QComboBox()
        form_layout.addRow(QLabel("Working Frame:"), self.working_frame_combo_box)

        # TCP Frame
        self.tcp_combo_box = QComboBox()
        form_layout.addRow(QLabel("TCP Frame:"), self.tcp_combo_box)

        # TCP Offset
        self.tcp_offset_combo_box = QComboBox()
        form_layout.addRow(QLabel("TCP Offset:"), self.tcp_offset_combo_box)

        # State
        self.state_combo_box = QComboBox()
        form_layout.addRow(QLabel("State:"), self.state_combo_box)

        # Reload button
        self.reload_push_button = QPushButton("Reload")
        form_layout.addRow(QLabel(""), self.reload_push_button)

        layout.addWidget(frame)
        self.tab_widget.addTab(tab, "Config")

    def _create_joint_tab(self):
        """Create joint control tab."""
        tab = QWidget()
        tab.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(3, 3, 3, 3)

        # Joint state slider widget
        if JointSliderWidget is not None:
            self.joint_state_slider = JointSliderWidget()
            self.joint_state_slider.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            layout.addWidget(self.joint_state_slider)
        else:
            # Placeholder
            placeholder = QLabel("JointSliderWidget not available")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(placeholder)

        # Vertical spacer
        layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        self.tab_widget.addTab(tab, "Joint")

    def _create_cartesian_tab(self):
        """Create cartesian control tab."""
        tab = QWidget()
        tab.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(3, 3, 3, 3)

        # Cartesian editor widget placeholder
        self.cartesian_widget = QLabel("Cartesian Editor Widget")
        self.cartesian_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cartesian_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.cartesian_widget)

        # Vertical spacer
        layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        self.tab_widget.addTab(tab, "Cartesian")

    def _create_state_tab(self):
        """Create state tab."""
        tab = QWidget()
        tab.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(3, 3, 3, 3)

        # Scene state widget placeholder
        self.state_widget = QLabel("Scene State Widget")
        self.state_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
        )
        layout.addWidget(self.state_widget)

        self.tab_widget.addTab(tab, "State")
