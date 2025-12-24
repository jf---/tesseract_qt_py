"""IK solver widget."""
from __future__ import annotations

import numpy as np
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QComboBox,
    QDoubleSpinBox,
    QPushButton,
    QLabel,
    QGroupBox,
    QFrame,
)

from tesseract_robotics.tesseract_kinematics import KinGroupIKInput


class IKWidget(QWidget):
    """Inverse kinematics solver widget."""

    solutionFound = Signal(dict)  # joint_name -> value
    targetPoseSet = Signal(object)  # target pose (Isometry3d)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._env = None
        self._kin_group = None
        self._link_names = []
        self._joint_names = []
        self._joint_limits = {}  # joint_name -> (lower, upper)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Target pose inputs
        pose_group = QGroupBox("Target Pose")
        pose_layout = QFormLayout(pose_group)

        self.x_spin = self._create_spinbox(-10, 10, 0.001)
        self.y_spin = self._create_spinbox(-10, 10, 0.001)
        self.z_spin = self._create_spinbox(-10, 10, 0.001)
        self.roll_spin = self._create_spinbox(-3.14159, 3.14159, 0.01)
        self.yaw_spin = self._create_spinbox(-3.14159, 3.14159, 0.01)
        self.pitch_spin = self._create_spinbox(-3.14159, 3.14159, 0.01)

        pose_layout.addRow("X:", self.x_spin)
        pose_layout.addRow("Y:", self.y_spin)
        pose_layout.addRow("Z:", self.z_spin)
        pose_layout.addRow("Roll:", self.roll_spin)
        pose_layout.addRow("Pitch:", self.pitch_spin)
        pose_layout.addRow("Yaw:", self.yaw_spin)

        layout.addWidget(pose_group)

        # End effector selection
        ee_group = QGroupBox("End Effector")
        ee_layout = QFormLayout(ee_group)

        self.link_combo = QComboBox()
        ee_layout.addRow("Link:", self.link_combo)

        layout.addWidget(ee_group)

        # Solve button
        btn_layout = QHBoxLayout()
        self.solve_btn = QPushButton("Solve IK")
        self.solve_btn.clicked.connect(self._solve_ik)
        btn_layout.addWidget(self.solve_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Status
        self.status_label = QLabel("No solution")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        layout.addStretch()

    def _create_spinbox(self, min_val: float, max_val: float, step: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setSingleStep(step)
        spin.setDecimals(4)
        spin.setFixedWidth(100)
        return spin

    def set_environment(self, env):
        """Set tesseract environment."""
        self._env = env
        if env is None:
            return

        sg = env.getSceneGraph()
        self._link_names = [link.getName() for link in sg.getLinks()]
        self.link_combo.clear()
        self.link_combo.addItems(self._link_names)

        # Get movable joints and limits for numerical IK fallback
        from tesseract_robotics.tesseract_scene_graph import JointType
        movable_types = (JointType.REVOLUTE, JointType.CONTINUOUS, JointType.PRISMATIC)
        self._joint_names = []
        self._joint_limits = {}
        for joint in sg.getJoints():
            if joint.type in movable_types:
                name = joint.getName()
                self._joint_names.append(name)
                lim = joint.limits
                self._joint_limits[name] = (lim.lower, lim.upper)

        # Try to get kinematic group (may fail if plugins not loaded)
        try:
            kin_info = env.getKinematicsInformation()
            if kin_info and kin_info.chain_groups:
                group_names = list(kin_info.chain_groups.keys())
                if group_names:
                    self._kin_group = env.getKinematicGroup(group_names[0])
                    if self._kin_group:
                        self._joint_names = list(self._kin_group.getJointNames())
                        tip_names = self._kin_group.getAllPossibleTipLinkNames()
                        if tip_names:
                            self.link_combo.clear()
                            self.link_combo.addItems(tip_names)
        except Exception as e:
            print(f"Kinematic group unavailable (using numerical IK): {e}")
            self._kin_group = None
            # Set tool0 as default TCP if it exists
            if "tool0" in self._link_names:
                self.link_combo.setCurrentText("tool0")

    def _solve_ik(self):
        """Solve IK for target pose."""
        if self._env is None:
            self.status_label.setText("No environment loaded")
            self.status_label.setStyleSheet("color: red;")
            return

        # Use numerical IK if kinematic group not available
        if self._kin_group is None:
            self._solve_ik_numerical()
            return

        try:
            # Get target pose from UI
            x = self.x_spin.value()
            y = self.y_spin.value()
            z = self.z_spin.value()
            roll = self.roll_spin.value()
            pitch = self.pitch_spin.value()
            yaw = self.yaw_spin.value()

            # Convert RPY to transform
            from scipy.spatial.transform import Rotation
            rot = Rotation.from_euler('xyz', [roll, pitch, yaw])
            rot_matrix = rot.as_matrix()

            # Create Eigen Isometry3d
            import tesseract_robotics.tesseract_common as tc
            target = tc.Isometry3d.Identity()
            target.translation = np.array([x, y, z])
            target.linear = rot_matrix

            # Emit target pose for visualization
            self.targetPoseSet.emit(target)

            # Get end effector link
            tcp_name = self.link_combo.currentText()
            if not tcp_name:
                self.status_label.setText("No TCP selected")
                self.status_label.setStyleSheet("color: red;")
                return

            # Get working frame (base link)
            base_names = self._kin_group.getAllPossibleBaseLinkNames()
            working_frame = base_names[0] if base_names else "base_link"

            # Create IK input
            ik_input = KinGroupIKInput(target, working_frame, tcp_name)

            # Get seed from current state
            state = self._env.getState()
            seed = np.zeros(len(self._joint_names))
            for i, jname in enumerate(self._joint_names):
                try:
                    seed[i] = state.joints[jname]
                except (KeyError, AttributeError):
                    seed[i] = 0.0

            # Solve IK
            solutions = self._kin_group.calcInvKin(ik_input, seed)

            if not solutions or len(solutions) == 0:
                self.status_label.setText("No solution found")
                self.status_label.setStyleSheet("color: red;")
                return

            # Find closest solution to seed
            best_sol = solutions[0]
            best_dist = np.linalg.norm(best_sol - seed)

            for sol in solutions[1:]:
                dist = np.linalg.norm(sol - seed)
                if dist < best_dist:
                    best_sol = sol
                    best_dist = dist

            # Check limits
            limits = self._kin_group.getLimits()
            joint_limits = limits.joint_limits

            within_limits = True
            for i, (jname, val) in enumerate(zip(self._joint_names, best_sol)):
                if jname in joint_limits:
                    jlim = joint_limits[jname]
                    if val < jlim.lower or val > jlim.upper:
                        within_limits = False
                        break

            if not within_limits:
                self.status_label.setText(f"Solution found but violates limits (dist={best_dist:.4f})")
                self.status_label.setStyleSheet("color: orange;")
            else:
                self.status_label.setText(f"Solution found! (dist={best_dist:.4f})")
                self.status_label.setStyleSheet("color: green;")

            # Emit solution
            joint_values = {name: float(val) for name, val in zip(self._joint_names, best_sol)}
            self.solutionFound.emit(joint_values)

        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            print(f"IK solve error: {e}")
            import traceback
            traceback.print_exc()

    def _solve_ik_numerical(self):
        """Solve IK numerically using scipy optimization."""
        from scipy.optimize import minimize
        from scipy.spatial.transform import Rotation
        import tesseract_robotics.tesseract_common as tc

        try:
            # Get target pose from UI
            target_pos = np.array([self.x_spin.value(), self.y_spin.value(), self.z_spin.value()])
            target_rpy = np.array([self.roll_spin.value(), self.pitch_spin.value(), self.yaw_spin.value()])
            target_rot = Rotation.from_euler('xyz', target_rpy)

            # Emit target for visualization (construct from 4x4 matrix)
            mat = np.eye(4)
            mat[:3, :3] = target_rot.as_matrix()
            mat[:3, 3] = target_pos
            target = tc.Isometry3d(mat)
            self.targetPoseSet.emit(target)

            tcp_link = self.link_combo.currentText()
            if not tcp_link:
                self.status_label.setText("No TCP link selected")
                self.status_label.setStyleSheet("color: red;")
                return

            # Get current joint values as seed
            state = self._env.getState()
            seed = np.array([state.joints.get(j, 0.0) for j in self._joint_names])

            # Build bounds
            bounds = [(self._joint_limits[j][0], self._joint_limits[j][1]) for j in self._joint_names]

            def cost_fn(q):
                """Cost = position error + orientation error."""
                # Set joints and get FK
                joint_dict = {name: float(val) for name, val in zip(self._joint_names, q)}
                self._env.setState(joint_dict)
                fk_state = self._env.getState()

                try:
                    tcp_tf = fk_state.link_transforms[tcp_link]
                    tcp_pos = np.array(tcp_tf.translation())
                    tcp_rot = Rotation.from_matrix(tcp_tf.rotation())
                except (KeyError, AttributeError):
                    return 1e6

                # Position error
                pos_err = np.linalg.norm(tcp_pos - target_pos)

                # Orientation error (angle between rotations)
                rot_diff = target_rot.inv() * tcp_rot
                angle_err = np.abs(rot_diff.magnitude())

                return pos_err + 0.5 * angle_err

            # Optimize
            result = minimize(cost_fn, seed, method='SLSQP', bounds=bounds,
                              options={'maxiter': 100, 'ftol': 1e-6})

            # Restore original state
            self._env.setState({name: float(val) for name, val in zip(self._joint_names, seed)})

            if result.fun < 0.01:  # Success threshold
                self.status_label.setText(f"Solution found! (err={result.fun:.4f})")
                self.status_label.setStyleSheet("color: green;")
                joint_values = {name: float(val) for name, val in zip(self._joint_names, result.x)}
                self.solutionFound.emit(joint_values)
            else:
                self.status_label.setText(f"No good solution (err={result.fun:.4f})")
                self.status_label.setStyleSheet("color: orange;")

        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("color: red;")
            import traceback
            traceback.print_exc()

    def set_target_from_fk(self, pose):
        """Set target pose from forward kinematics result."""
        try:
            # Extract translation
            trans = pose.translation
            self.x_spin.setValue(float(trans[0]))
            self.y_spin.setValue(float(trans[1]))
            self.z_spin.setValue(float(trans[2]))

            # Extract rotation as RPY
            from scipy.spatial.transform import Rotation
            rot_matrix = pose.linear
            rot = Rotation.from_matrix(rot_matrix)
            rpy = rot.as_euler('xyz')

            self.roll_spin.setValue(float(rpy[0]))
            self.pitch_spin.setValue(float(rpy[1]))
            self.yaw_spin.setValue(float(rpy[2]))

        except Exception as e:
            print(f"Failed to set target from FK: {e}")
