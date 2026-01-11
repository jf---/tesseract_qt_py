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
    from widgets.fkik_widget import FKIKWidget
except ImportError:
    FKIKWidget = None


class ManipulationWidget(QWidget):
    """Widget for robot manipulation control with FK/IK combined."""

    # Signals
    configChanged = Signal()
    groupChanged = Signal(str)  # group name
    reloadRequested = Signal()
    stateApplyRequested = Signal(str)  # state name
    jointValuesChanged = Signal(dict)  # joint values from FK/IK
    ikSolveRequested = Signal()  # IK solve completed

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._env = None
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
        self._create_fkik_tab()
        self._create_config_tab()
        self._create_state_tab()

    def _create_fkik_tab(self):
        """Create unified FK/IK control tab."""
        if FKIKWidget is not None:
            self.fkik_widget = FKIKWidget()
            self.fkik_widget.setSizePolicy(
                QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding
            )
            self.tab_widget.addTab(self.fkik_widget, "FK / IK")
        else:
            # Placeholder
            placeholder = QLabel("FKIKWidget not available")
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.fkik_widget = None
            self.tab_widget.addTab(placeholder, "FK / IK")

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

        # Group Name
        self.group_combo_box = QComboBox()
        self.group_combo_box.setToolTip("Kinematic group for IK solving (from SRDF)")
        form_layout.addRow(QLabel("Group Name:"), self.group_combo_box)

        # Working Frame
        self.working_frame_combo_box = QComboBox()
        self.working_frame_combo_box.setToolTip("Reference frame for motion commands")
        form_layout.addRow(QLabel("Working Frame:"), self.working_frame_combo_box)

        # TCP Frame
        self.tcp_combo_box = QComboBox()
        self.tcp_combo_box.setToolTip("Tool Center Point link for pose display")
        form_layout.addRow(QLabel("TCP Frame:"), self.tcp_combo_box)

        # TCP Offset
        self.tcp_offset_combo_box = QComboBox()
        self.tcp_offset_combo_box.setToolTip("Additional offset from TCP link")
        form_layout.addRow(QLabel("TCP Offset:"), self.tcp_offset_combo_box)

        # State
        self.state_combo_box = QComboBox()
        self.state_combo_box.setToolTip("Named joint configurations from SRDF")
        form_layout.addRow(QLabel("State:"), self.state_combo_box)

        # Reload button
        self.reload_push_button = QPushButton("Reload")
        self.reload_push_button.setToolTip("Reload environment from files")
        form_layout.addRow(QLabel(""), self.reload_push_button)

        layout.addWidget(frame)
        layout.addStretch()
        self.tab_widget.addTab(tab, "Config")

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
        # Config changed signals
        self.group_combo_box.currentTextChanged.connect(self._on_group_changed)
        self.working_frame_combo_box.currentIndexChanged.connect(lambda: self.configChanged.emit())
        self.tcp_combo_box.currentIndexChanged.connect(self._on_tcp_changed)
        self.tcp_offset_combo_box.currentIndexChanged.connect(lambda: self.configChanged.emit())

        # Reload button
        self.reload_push_button.clicked.connect(self.reloadRequested.emit)

        # State apply button
        self.apply_state_button.clicked.connect(self._on_apply_state)

        # FK/IK widget signals
        if self.fkik_widget is not None:
            self.fkik_widget.jointValuesChanged.connect(self.jointValuesChanged.emit)
            self.fkik_widget.ikSolveRequested.connect(self.ikSolveRequested.emit)

    def _on_group_changed(self, group_name: str):
        """Handle group selection change."""
        if group_name:
            self.groupChanged.emit(group_name)
            self.configChanged.emit()
            # Update FK/IK widget with new group
            self._update_fkik_environment()

    def _on_tcp_changed(self):
        """Handle TCP selection change."""
        self.configChanged.emit()
        self._update_fkik_environment()

    def _update_fkik_environment(self):
        """Update FK/IK widget with current environment settings."""
        if self.fkik_widget is None or self._env is None:
            return
        group = self.group_combo_box.currentText()
        tcp = self.tcp_combo_box.currentText()
        if tcp:  # TCP is required, group is optional (will auto-create chain)
            self.fkik_widget.set_environment(self._env, group, tcp)

    def _on_apply_state(self):
        """Handle apply state button click."""
        state = self.state_selector_combo.currentText()
        if state:
            self.stateApplyRequested.emit(state)

    def set_environment(self, env):
        """Set the tesseract environment for FK/IK computations."""
        self._env = env
        self._update_fkik_environment()

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
        if self.fkik_widget is not None:
            self.fkik_widget.set_joints(joints)

    def set_joint_values(self, values: dict[str, float], emit_signal: bool = True):
        """Set current joint values.

        Args:
            values: Dict mapping joint name to value (radians)
            emit_signal: If False, suppresses external signal
        """
        if self.fkik_widget is not None:
            self.fkik_widget.set_joint_values(values, emit_signal=emit_signal)

    def get_joint_values(self) -> dict[str, float]:
        """Get current joint values from slider.

        Returns:
            Dict mapping joint name to value (radians)
        """
        if self.fkik_widget is not None:
            return self.fkik_widget.get_joint_values()
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

    def get_cartesian_pose(self) -> tuple[float, float, float, float, float, float] | None:
        """Get Cartesian editor pose (angles in radians)."""
        if self.fkik_widget is not None:
            return self.fkik_widget.get_cartesian_pose()
        return None
