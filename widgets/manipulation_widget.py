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
    groupChanged = Signal(str)  # group name
    reloadRequested = Signal()
    stateApplyRequested = Signal(str)  # state name
    jointValuesChanged = Signal(dict)  # joint values from slider

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._setup_ui()
        self._connect_signals()
        # Initialize tab enabled state for default mode (Joint)
        self._on_mode_changed(0)

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
        self.group_combo_box.currentTextChanged.connect(self._on_group_changed)
        self.working_frame_combo_box.currentIndexChanged.connect(lambda: self.configChanged.emit())
        self.tcp_combo_box.currentIndexChanged.connect(lambda: self.configChanged.emit())
        self.tcp_offset_combo_box.currentIndexChanged.connect(lambda: self.configChanged.emit())

        # Reload button
        self.reload_push_button.clicked.connect(self.reloadRequested.emit)

        # State apply button
        self.apply_state_button.clicked.connect(self._on_apply_state)

        # Joint slider values
        if hasattr(self, 'joint_state_slider') and self.joint_state_slider is not None:
            self.joint_state_slider.jointValuesChanged.connect(self.jointValuesChanged.emit)

    def _on_group_changed(self, group_name: str):
        """Handle group selection change."""
        if group_name:
            self.groupChanged.emit(group_name)
            self.configChanged.emit()

    def _on_apply_state(self):
        """Handle apply state button click."""
        state = self.state_selector_combo.currentText()
        if state:
            self.stateApplyRequested.emit(state)

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

    def set_groups(self, groups):
        """Set available kinematic groups.

        Args:
            groups: List of group names
        """
        self.group_combo_box.clear()
        self.group_combo_box.addItems(groups)

    def set_states(self, states: list[str]):
        """Set available states for state selector.

        Args:
            states: List of state names
        """
        self.state_combo_box.clear()
        self.state_combo_box.addItems(states)
        self.state_selector_combo.clear()
        self.state_selector_combo.addItems(states)

    def set_joint_limits(self, joints: dict[str, tuple[float, float, float]]):
        """Set joints with limits for joint slider.

        Args:
            joints: Dict mapping joint name to (lower, upper, current)
        """
        if hasattr(self, 'joint_state_slider') and self.joint_state_slider is not None:
            self.joint_state_slider.set_joints(joints)

    def set_joint_values(self, values: dict[str, float]):
        """Set current joint values.

        Args:
            values: Dict mapping joint name to value (radians)
        """
        if hasattr(self, 'joint_state_slider') and self.joint_state_slider is not None:
            self.joint_state_slider.set_values(values)

    def get_joint_values(self) -> dict[str, float]:
        """Get current joint values from slider.

        Returns:
            Dict mapping joint name to value (radians)
        """
        if hasattr(self, 'joint_state_slider') and self.joint_state_slider is not None:
            return self.joint_state_slider.get_values()
        return {}

    def current_group(self) -> str:
        """Get currently selected group name."""
        return self.group_combo_box.currentText()

    def current_tcp(self) -> str:
        """Get currently selected TCP link."""
        return self.tcp_combo_box.currentText()

    def current_working_frame(self) -> str:
        """Get currently selected working frame."""
        return self.working_frame_combo_box.currentText()
