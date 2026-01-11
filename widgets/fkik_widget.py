"""Unified FK/IK widget with bidirectional sync."""

from __future__ import annotations

from math import atan2

import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QGroupBox,
    QLabel,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from widgets.cartesian_editor import CartesianEditorWidget
from widgets.joint_slider import JointSliderWidget


def rotation_to_rpy(rotation: np.ndarray) -> tuple[float, float, float]:
    """Convert 3x3 rotation matrix to roll-pitch-yaw (radians)."""
    sy = -rotation[2, 0]
    cy = np.sqrt(rotation[0, 0] ** 2 + rotation[1, 0] ** 2)

    if cy > 1e-6:
        roll = atan2(rotation[2, 1], rotation[2, 2])
        pitch = atan2(sy, cy)
        yaw = atan2(rotation[1, 0], rotation[0, 0])
    else:
        # Gimbal lock
        roll = atan2(-rotation[1, 2], rotation[1, 1])
        pitch = atan2(sy, cy)
        yaw = 0.0

    return roll, pitch, yaw


class FKIKWidget(QWidget):
    """Unified FK/IK widget with bidirectional sync.

    FK slider changes -> update IK sliders (real-time)
    IK solve button -> update FK sliders
    Both directions suppress external signals during sync.
    """

    # External signals (emitted only on user-initiated changes)
    jointValuesChanged = Signal(dict)  # User moved FK slider
    ikSolveRequested = Signal()  # User clicked Solve IK (after solution applied)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._env = None
        self._group_name: str = ""  # Store name, not object (becomes invalid after setState)
        self._tcp_link: str = ""
        self._joint_names: list[str] = []
        self._syncing = False  # Prevents bidirectional loops

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Vertical)

        # FK section (Joint Sliders)
        fk_group = QGroupBox("Joint Space (FK)")
        fk_layout = QVBoxLayout(fk_group)
        fk_layout.setContentsMargins(3, 3, 3, 3)
        self.joint_slider = JointSliderWidget()
        fk_layout.addWidget(self.joint_slider)
        splitter.addWidget(fk_group)

        # IK section (Cartesian Editor)
        ik_group = QGroupBox("Cartesian Space (IK)")
        ik_layout = QVBoxLayout(ik_group)
        ik_layout.setContentsMargins(3, 3, 3, 3)
        self.cartesian_widget = CartesianEditorWidget()
        ik_layout.addWidget(self.cartesian_widget)
        splitter.addWidget(ik_group)

        # Set initial sizes (FK gets more space)
        splitter.setSizes([300, 200])

        layout.addWidget(splitter)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray; font-size: 10px;")
        layout.addWidget(self.status_label)

    def _connect_signals(self):
        """Connect internal signals."""
        # FK changes -> update IK display
        self.joint_slider.jointValuesChanged.connect(self._on_fk_changed)

        # IK slider changes -> solve IK in real-time
        self.cartesian_widget.poseChanged.connect(self._on_ik_pose_changed)

    def set_environment(self, env, group_name: str = "", tcp_link: str = ""):
        """Set environment and kinematic group for FK/IK computations.

        Args:
            env: Tesseract Environment
            group_name: Kinematic group name (e.g., 'manipulator'), or empty to auto-detect
            tcp_link: TCP link name (e.g., 'tool0')
        """
        self._env = env
        self._tcp_link = tcp_link
        self._group_name = group_name

        if env is None:
            self._joint_names = []
            return

        try:
            # Get fresh kinematic group to extract joint names
            # Note: Don't store the group object - it becomes invalid after env.setState()
            if group_name:
                kin_group = env.getKinematicGroup(group_name)
                if kin_group:
                    self._joint_names = list(kin_group.getJointNames())
                else:
                    self._joint_names = []
            else:
                self._joint_names = []

            # Initialize IK display from current joint values
            if self._joint_names:
                self._update_ik_from_fk(self.joint_slider.get_values())

        except Exception as e:
            self._joint_names = []
            self.status_label.setText(f"No kinematics: {e}")

    def _create_chain_group(self, env, tcp_link: str):
        """Create a kinematic group from base_link to tcp_link."""
        try:

            sg = env.getSceneGraph()

            # Find base link (root of scene graph)
            base_link = sg.getRoot()

            # Try creating via environment's kinematic factory
            factory = env.getKinematicsFactory()
            if factory:
                group = factory.createKinGroup(sg, base_link, tcp_link)
                if group:
                    return group
        except Exception:
            pass
        return None

    def set_joints(self, joints: dict[str, tuple[float, float, float]]):
        """Setup joint sliders.

        Args:
            joints: Dict mapping joint name to (lower, upper, current) limits
        """
        self.joint_slider.set_joints(joints)
        # Update IK display with initial pose
        self._update_ik_from_fk(self.joint_slider.get_values())

    def set_joint_values(self, values: dict[str, float], emit_signal: bool = True):
        """Set joint values programmatically.

        Args:
            values: Joint name -> value (radians)
            emit_signal: If False, suppresses external signal
        """
        if not emit_signal:
            self._syncing = True

        self.joint_slider.set_values(values)

        if not emit_signal:
            self._syncing = False
            # Still update IK display
            self._update_ik_from_fk(values)

    def get_joint_values(self) -> dict[str, float]:
        """Get current joint values."""
        return self.joint_slider.get_values()

    def _on_fk_changed(self, joint_values: dict[str, float]):
        """Handle FK slider change - update IK display, emit signal."""
        if self._syncing:
            return

        self._syncing = True

        # Update IK sliders to show current TCP pose
        self._update_ik_from_fk(joint_values)

        self._syncing = False

        # Emit signal for external listeners (rendering, collision, etc.)
        self.jointValuesChanged.emit(joint_values)

    def _update_ik_from_fk(self, joint_values: dict[str, float]):
        """Compute FK and update Cartesian display."""
        if self._env is None or not self._tcp_link:
            return

        try:
            # Set joint state and get TCP transform
            self._env.setState(joint_values)
            state = self._env.getState()
            tcp_tf = state.link_transforms.get(self._tcp_link)

            if tcp_tf is not None:
                # Extract position
                trans = tcp_tf.translation()
                x, y, z = float(trans[0]), float(trans[1]), float(trans[2])

                # Extract rotation and convert to RPY
                rot = tcp_tf.rotation()
                roll, pitch, yaw = rotation_to_rpy(rot)

                # Update Cartesian widget (suppresses its signals via _updating)
                self.cartesian_widget.set_pose(x, y, z, roll, pitch, yaw)

        except Exception as e:
            self.status_label.setText(f"FK: {e}")

    def _on_ik_pose_changed(
        self, x: float, y: float, z: float, roll: float, pitch: float, yaw: float
    ):
        """Handle real-time IK pose change from Cartesian sliders."""
        if self._syncing:
            return
        # Delegate to IK solve
        self._on_ik_solve_requested()

    def _on_ik_solve_requested(self):
        """Handle IK solve button - solve and update FK sliders."""
        if self._syncing:
            return

        if not self._group_name or self._env is None:
            self.status_label.setText("No kinematics available")
            self.status_label.setStyleSheet("color: red; font-size: 10px;")
            return

        self._syncing = True

        try:
            import tesseract_robotics.tesseract_common as tc
            from scipy.spatial.transform import Rotation
            from tesseract_robotics.tesseract_kinematics import KinGroupIKInput

            # Get fresh kinematic group (stored ref becomes invalid after setState)
            kin_group = self._env.getKinematicGroup(self._group_name)
            if kin_group is None:
                self.status_label.setText("No kinematic group")
                self.status_label.setStyleSheet("color: red; font-size: 10px;")
                self._syncing = False
                return

            # Get target pose from Cartesian widget
            x, y, z, roll, pitch, yaw = self.cartesian_widget.get_pose()

            # Build target transform using scipy (more robust)
            rot = Rotation.from_euler("xyz", [roll, pitch, yaw])
            mat = np.eye(4)
            mat[:3, :3] = rot.as_matrix()
            mat[:3, 3] = [x, y, z]
            tf = tc.Isometry3d(mat)

            # Get working frame and create IK input
            working_frame = kin_group.getBaseLinkName()
            ik_input = KinGroupIKInput(tf, working_frame, self._tcp_link)

            # Get seed from current state
            state = self._env.getState()
            seed = np.zeros(len(self._joint_names))
            for i, jname in enumerate(self._joint_names):
                try:
                    seed[i] = state.joints[jname]
                except (KeyError, AttributeError):
                    seed[i] = 0.0

            # Solve IK
            solutions = kin_group.calcInvKin(ik_input, seed)

            if solutions and len(solutions) > 0:
                # Use first solution
                sol = solutions[0]
                joint_values = {
                    self._joint_names[i]: float(sol[i]) for i in range(len(self._joint_names))
                }

                # Update FK sliders (without emitting their signal)
                for name, value in joint_values.items():
                    if name in self.joint_slider.sliders:
                        self.joint_slider.sliders[name].set_value(value)

                self.status_label.setText("IK solved")
                self.status_label.setStyleSheet("color: green; font-size: 10px;")

                self._syncing = False
                # Emit joint values (for rendering update)
                self.jointValuesChanged.emit(joint_values)
                self.ikSolveRequested.emit()
            else:
                self.status_label.setText("IK: No solution")
                self.status_label.setStyleSheet("color: orange; font-size: 10px;")
                self._syncing = False

        except Exception as e:
            self.status_label.setText(f"IK: {e}")
            self.status_label.setStyleSheet("color: red; font-size: 10px;")
            self._syncing = False

    def get_cartesian_pose(self) -> tuple[float, float, float, float, float, float]:
        """Get current Cartesian pose (x, y, z, roll, pitch, yaw in radians)."""
        return self.cartesian_widget.get_pose()
