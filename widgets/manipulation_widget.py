"""Manipulation widget for robot control."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
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
    from widgets.joint_slider import JointSliderWidget
except ImportError:
    JointSliderWidget = None

try:
    from widgets.cartesian_editor import CartesianEditorWidget
except ImportError:
    CartesianEditorWidget = None


class ManipulationWidget(QWidget):
    """Widget for robot manipulation control with multiple modes."""

    # Signals
    configChanged = Signal()
    modeChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._setup_ui()
        self._connect_signals()

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

        # Cartesian editor widget
        if CartesianEditorWidget is not None:
            self.cartesian_widget = CartesianEditorWidget()
            self.cartesian_widget.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            layout.addWidget(self.cartesian_widget)
        else:
            # Placeholder
            self.cartesian_widget = QLabel("CartesianEditorWidget not available")
            self.cartesian_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
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

        # State selector
        form_layout = QFormLayout()
        self.state_selector_combo = QComboBox()
        form_layout.addRow(QLabel("State:"), self.state_selector_combo)

        self.apply_state_button = QPushButton("Apply")
        form_layout.addRow(QLabel(""), self.apply_state_button)

        layout.addLayout(form_layout)

        # Vertical spacer
        layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        self.tab_widget.addTab(tab, "State")

    def _connect_signals(self):
        """Connect widget signals."""
        # Mode changed
        self.mode_combo_box.currentIndexChanged.connect(self._on_mode_changed)

        # Config changed signals
        self.group_combo_box.currentIndexChanged.connect(lambda: self.configChanged.emit())
        self.working_frame_combo_box.currentIndexChanged.connect(lambda: self.configChanged.emit())
        self.tcp_combo_box.currentIndexChanged.connect(lambda: self.configChanged.emit())
        self.tcp_offset_combo_box.currentIndexChanged.connect(lambda: self.configChanged.emit())

    def _on_mode_changed(self, index):
        """Handle mode change and enable/disable tabs."""
        if index == 0:  # Joint mode
            self.tab_widget.setTabEnabled(1, True)  # Joint tab
            self.tab_widget.setTabEnabled(2, False)  # Cartesian tab
        else:  # Cartesian mode
            self.tab_widget.setTabEnabled(1, False)  # Joint tab
            self.tab_widget.setTabEnabled(2, True)  # Cartesian tab

        self.modeChanged.emit(index)

    def set_links(self, links):
        """Set available links for working frame and TCP selection.

        Args:
            links: List of link names
        """
        self.working_frame_combo_box.clear()
        self.tcp_combo_box.clear()
        self.working_frame_combo_box.addItems(links)
        self.tcp_combo_box.addItems(links)

    def set_joints(self, joints):
        """Set available joints.

        Args:
            joints: List of joint names
        """
        # Update joint slider if available
        if hasattr(self, 'joint_state_slider') and JointSliderWidget is not None:
            # Joint slider handles joint configuration
            pass

    def set_groups(self, groups):
        """Set available kinematic groups.

        Args:
            groups: List of group names
        """
        self.group_combo_box.clear()
        self.group_combo_box.addItems(groups)
