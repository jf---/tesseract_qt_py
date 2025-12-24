"""Tesseract Qt Viewer."""
from __future__ import annotations

import sys
import os

# CRITICAL: macOS VTK+Qt setup - NO X11
if sys.platform == 'darwin':
    os.environ.pop('DISPLAY', None)
    os.environ['QT_QPA_PLATFORM'] = 'cocoa'

# Force QOpenGLWidget base for VTK - required for rendering to work
import vtkmodules.qt
vtkmodules.qt.QVTKRWIBase = "QOpenGLWidget"

from loguru import logger
logger.add("/tmp/tesseract_viewer.log", rotation="1 MB", level="DEBUG")
logger.info("Starting tesseract_qt_py viewer")

# Log uncaught exceptions
def _excepthook(exc_type, exc_value, exc_tb):
    logger.opt(exception=(exc_type, exc_value, exc_tb)).error("Uncaught exception")
sys.excepthook = _excepthook

from pathlib import Path

from PySide6.QtCore import Qt, QSettings
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QDockWidget, QFileDialog, QMessageBox, QStatusBar,
    QInputDialog, QLabel,
)
from PySide6.QtGui import QAction, QKeySequence, QShortcut

from tesseract_robotics.tesseract_environment import Environment
from tesseract_robotics.tesseract_common import GeneralResourceLocator, FilesystemPath, CollisionMarginData
from tesseract_robotics.tesseract_scene_graph import JointType
from tesseract_robotics.tesseract_collision import (
    ContactRequest, ContactResultMap, ContactResultVector, ContactTestType,
    ContactManagersPluginFactory,
)
from tesseract_robotics.tesseract_common import _FilesystemPath

from widgets.render_widget import RenderWidget
from widgets.scene_tree import SceneTreeWidget
from widgets.ik_widget import IKWidget
from widgets.info_panel import RobotInfoPanel
from widgets.trajectory_player import TrajectoryPlayerWidget
from widgets.contact_compute_widget import ContactComputeWidget
from widgets.plot_widget import PlotWidget
from widgets.acm_editor import ACMEditorWidget
from widgets.kinematic_groups_editor import KinematicGroupsEditorWidget
from widgets.manipulation_widget import ManipulationWidget
from widgets.group_states_editor import GroupStatesEditorWidget
from widgets.tcp_editor import TCPEditorWidget
from widgets.task_composer_widget import TaskComposerWidget
from widgets.log_widget import LogWidget
from core.state_manager import StateManager


class TesseractViewer(QMainWindow):
    """Main viewer window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tesseract Viewer")
        self.resize(1400, 800)
        self.setMinimumSize(800, 600)
        self._env = None
        self._paths = (None, None)  # urdf, srdf
        self._joint_limits = {}  # joint name -> (lower, upper, current)
        self._settings = QSettings("tesseract_qt", "viewer")
        self._recent_actions = []
        self.state_mgr = StateManager()
        self._setup()
        self._setup_status_logging()

    def _setup_status_logging(self):
        """Setup loguru to also show messages in status bar with copy context menu."""
        from PySide6.QtWidgets import QStatusBar, QApplication, QLabel
        from PySide6.QtGui import QAction
        from PySide6.QtCore import Qt

        # Create custom status bar with context menu
        status_bar = QStatusBar()
        status_bar.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)

        copy_action = QAction("Copy Message", status_bar)
        copy_action.triggered.connect(lambda: QApplication.clipboard().setText(status_bar.currentMessage()))
        status_bar.addAction(copy_action)

        # TCP pose label - must be created here before setStatusBar() for proper Qt ownership
        self._tcp_pose_label = QLabel("TCP: --", status_bar)
        self._tcp_pose_label.setStyleSheet("padding-right: 10px; color: #666;")
        status_bar.addPermanentWidget(self._tcp_pose_label)

        self.setStatusBar(status_bar)
        self._last_status_message = ""

        def status_sink(message):
            record = message.record
            level = record["level"].name
            text = record["message"]

            # Color coding by level
            colors = {
                "DEBUG": "#888888",
                "INFO": "#000000",
                "SUCCESS": "#228B22",
                "WARNING": "#FF8C00",
                "ERROR": "#DC143C",
                "CRITICAL": "#8B0000",
            }
            color = colors.get(level, "#000000")

            # Show in status bar with color
            self.statusBar().setStyleSheet(f"color: {color};")
            self.statusBar().showMessage(text, 5000)  # 5 second timeout
            self._last_status_message = text

        logger.add(status_sink, level="INFO", format="{message}")

        # Also send logs to log widget
        def log_widget_sink(message):
            record = message.record
            level = record["level"].name
            time_str = record["time"].strftime("%H:%M:%S")
            text = f"{time_str} {level:8} {record['message']}"
            self.log_widget.append_log(text, level)

        logger.add(log_widget_sink, level="DEBUG", format="{message}")

    def status(self, msg: str, level: str = "info"):
        """Show message in status bar and log it."""
        getattr(logger, level.lower())(msg)

    def _setup(self):
        # Widgets
        self.render = RenderWidget()
        self.setCentralWidget(self.render)

        self.tree_dock = QDockWidget("Scene", self)
        self.tree = SceneTreeWidget()
        self.tree_dock.setWidget(self.tree)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.tree_dock)

        self.ik_dock = QDockWidget("IK Solver", self)
        self.ik_widget = IKWidget()
        self.ik_dock.setWidget(self.ik_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.ik_dock)

        self.info_dock = QDockWidget("Robot Info", self)
        self.info_panel = RobotInfoPanel()
        self.info_dock.setWidget(self.info_panel)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.info_dock)

        self.contact_dock = QDockWidget("Contact Checker", self)
        self.contact_widget = ContactComputeWidget()
        self.contact_dock.setWidget(self.contact_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.contact_dock)

        self.acm_dock = QDockWidget("ACM Editor", self)
        self.acm_widget = ACMEditorWidget()
        self.acm_dock.setWidget(self.acm_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.acm_dock)

        self.kin_groups_dock = QDockWidget("Kinematic Groups", self)
        self.kin_groups_widget = KinematicGroupsEditorWidget()
        self.kin_groups_dock.setWidget(self.kin_groups_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.kin_groups_dock)

        self.manip_dock = QDockWidget("Manipulation", self)
        self.manip_widget = ManipulationWidget()
        self.manip_dock.setWidget(self.manip_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.manip_dock)

        self.group_states_dock = QDockWidget("Group States", self)
        self.group_states_widget = GroupStatesEditorWidget()
        self.group_states_dock.setWidget(self.group_states_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.group_states_dock)

        self.tcp_dock = QDockWidget("TCP Editor", self)
        self.tcp_widget = TCPEditorWidget()
        self.tcp_dock.setWidget(self.tcp_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.tcp_dock)

        self.task_composer_dock = QDockWidget("Task Composer", self)
        self.task_composer_widget = TaskComposerWidget()
        self.task_composer_dock.setWidget(self.task_composer_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.task_composer_dock)

        self.log_dock = QDockWidget("Logs", self)
        self.log_widget = LogWidget()
        self.log_dock.setWidget(self.log_widget)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.log_dock)

        # Tabify right panel docks (Manipulation first - has FK/IK)
        self.tabifyDockWidget(self.manip_dock, self.ik_dock)
        self.tabifyDockWidget(self.ik_dock, self.info_dock)
        self.tabifyDockWidget(self.info_dock, self.contact_dock)
        self.tabifyDockWidget(self.contact_dock, self.acm_dock)
        self.tabifyDockWidget(self.acm_dock, self.kin_groups_dock)
        self.tabifyDockWidget(self.kin_groups_dock, self.group_states_dock)
        self.tabifyDockWidget(self.group_states_dock, self.tcp_dock)
        self.tabifyDockWidget(self.tcp_dock, self.task_composer_dock)
        self.tabifyDockWidget(self.task_composer_dock, self.log_dock)
        self.manip_dock.raise_()

        self.traj_dock = QDockWidget("Trajectory Player", self)
        self.traj_player = TrajectoryPlayerWidget()
        self.traj_dock.setWidget(self.traj_player)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.traj_dock)

        self.plot_dock = QDockWidget("Joint Plot", self)
        self.plot = PlotWidget()
        self.plot_dock.setWidget(self.plot)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.plot_dock)
        self.tabifyDockWidget(self.traj_dock, self.plot_dock)
        self.traj_dock.raise_()

        # Set bottom dock area height
        self.resizeDocks([self.traj_dock], [180], Qt.Orientation.Vertical)

        # Menu
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction("Open URDF...", self._open_urdf, QKeySequence.StandardKey.Open)
        file_menu.addAction("Open SRDF...", self._open_srdf)
        file_menu.addSeparator()

        self._recent_menu = file_menu.addMenu("Recent Files")
        for i in range(10):
            act = QAction(self)
            act.setVisible(False)
            act.triggered.connect(lambda checked=False, idx=i: self._open_recent(idx))
            self._recent_actions.append(act)
            self._recent_menu.addAction(act)
        self._update_recent_menu()

        file_menu.addSeparator()
        file_menu.addAction("Load Trajectory...", self._load_trajectory)
        file_menu.addSeparator()
        file_menu.addAction("Reload", self._reload, QKeySequence.StandardKey.Refresh)
        file_menu.addSeparator()

        export_menu = file_menu.addMenu("Export")
        export_menu.addAction("Screenshot (PNG)...", self._export_screenshot)
        export_menu.addAction("Scene (STL)...", self._export_stl)
        export_menu.addAction("Scene (OBJ)...", self._export_obj)

        file_menu.addSeparator()
        file_menu.addAction("Quit", self.close, QKeySequence.StandardKey.Quit)

        state_menu = self.menuBar().addMenu("State")
        state_menu.addAction("Save Configuration...", self._save_config, QKeySequence("Ctrl+S"))
        state_menu.addAction("Load Configuration...", self._load_config, QKeySequence("Ctrl+O"))
        state_menu.addSeparator()
        state_menu.addAction("Save Pose As...", self._save_pose)
        state_menu.addAction("Load Pose...", self._load_pose)

        view_menu = self.menuBar().addMenu("View")
        view_menu.addAction(self.tree_dock.toggleViewAction())
        view_menu.addAction(self.manip_dock.toggleViewAction())
        view_menu.addAction(self.ik_dock.toggleViewAction())
        view_menu.addAction(self.info_dock.toggleViewAction())
        view_menu.addAction(self.traj_dock.toggleViewAction())
        view_menu.addAction(self.plot_dock.toggleViewAction())
        view_menu.addAction(self.contact_dock.toggleViewAction())
        view_menu.addAction(self.acm_dock.toggleViewAction())
        view_menu.addAction(self.kin_groups_dock.toggleViewAction())
        view_menu.addAction(self.group_states_dock.toggleViewAction())
        view_menu.addAction(self.tcp_dock.toggleViewAction())
        view_menu.addAction(self.task_composer_dock.toggleViewAction())
        view_menu.addAction(self.log_dock.toggleViewAction())
        view_menu.addSeparator()
        view_menu.addAction("Show Workspace...", self._show_workspace)
        view_menu.addAction("Clear Workspace", self._clear_workspace)

        # Connections - FK/IK from ManipulationWidget
        self.manip_widget.jointValuesChanged.connect(self.render.update_joint_values)
        self.manip_widget.jointValuesChanged.connect(self.info_panel.update_joint_values)
        self.manip_widget.jointValuesChanged.connect(self.ik_widget.update_current_tcp_pose)
        self.manip_widget.jointValuesChanged.connect(self._check_collisions_realtime)
        self.manip_widget.jointValuesChanged.connect(self._update_tcp_status)
        self.tree.linkSelected.connect(lambda n: (self.render.scene.highlight_link(n), self.render.render()))
        self.tree.linkSelected.connect(self.info_panel.set_tcp_link)
        self.tree.linkVisibilityChanged.connect(lambda n, v: (self.render.scene.set_link_visibility(n, v), self.render.render()))
        self.tree.linkFrameToggled.connect(lambda n, v: (self.render.scene.show_frame(n, v), self.render.render()))
        self.render.linkClicked.connect(self.tree.select_link)
        self.ik_widget.solutionFound.connect(lambda v: self.manip_widget.set_joint_values(v, emit_signal=True))
        self.ik_widget.targetPoseSet.connect(lambda pose: (self.render.scene.show_ik_target(pose), self.render.render()))
        self.traj_player.frameChanged.connect(self._on_trajectory_frame_changed)
        self.traj_player.frameChanged.connect(self.plot.set_frame_marker)
        self.ik_widget.planRequested.connect(self._plan_motion)
        self.tree.linkDeleteRequested.connect(self._delete_link)
        self.contact_widget.btn_compute.clicked.connect(self._compute_contacts)
        self.contact_widget.btn_check_state.clicked.connect(self._compute_contacts)
        self.contact_widget.btn_clear.clicked.connect(self._clear_contacts)
        self.acm_widget.entry_added.connect(self._on_acm_entry_added)
        self.acm_widget.entry_removed.connect(self._on_acm_entry_removed)
        self.acm_widget.generate_requested.connect(self._on_acm_generate)
        self.tcp_widget.tcp_changed.connect(self._on_tcp_changed)
        self.tcp_widget.offset_changed.connect(self._on_tcp_offset_changed)
        self.kin_groups_widget.group_added.connect(self._on_kin_group_added)
        self.kin_groups_widget.group_removed.connect(self._on_kin_group_removed)
        self.kin_groups_widget.group_modified.connect(self._on_kin_group_modified)
        self.group_states_widget.state_applied.connect(self._on_group_state_applied)
        self.group_states_widget.state_added.connect(self._on_group_state_added)
        self.task_composer_widget.execute_requested.connect(self._execute_task_composer)
        self.task_composer_widget.environment_push_button.clicked.connect(self._on_pick_environment)

        # Keyboard shortcuts
        self._setup_shortcuts()

    def load(self, urdf: str | Path, srdf: str | Path = None):
        """Load robot from URDF."""
        try:
            logger.info(f"Loading URDF: {urdf}")
            urdf_path = Path(urdf)

            # Auto-detect SRDF if not provided
            if not srdf:
                auto_srdf = urdf_path.with_suffix(".srdf")
                if auto_srdf.exists():
                    srdf = auto_srdf
                    logger.info(f"Auto-detected SRDF: {srdf}")

            self._paths = (urdf_path, Path(srdf) if srdf else None)
            self._env = Environment()
            loc = GeneralResourceLocator()

            if srdf:
                logger.info(f"Loading with SRDF: {srdf}")
                if not self._env.init(str(urdf), str(srdf), loc):
                    raise RuntimeError("Failed to init environment with SRDF")
            else:
                logger.info("Loading URDF only (no SRDF)")
                if not self._env.init(str(urdf), loc):
                    raise RuntimeError("Failed to init environment from URDF")

            logger.info("Environment initialized, loading into render widget")
            self.render.load_environment(self._env)
            logger.info("Render loaded, setting up tree")
            self.tree.load_environment(self._env)
            logger.info("Tree loaded, setting up manipulation widget")
            self.manip_widget.set_environment(self._env)
            logger.info("Setting up joints")
            self._setup_joints()
            logger.info("Joints setup, loading info panel")
            self.info_panel.load_environment(self._env)
            logger.info("Info panel loaded, detecting TCP link")
            tcp_link = self._detect_tcp_link()
            if tcp_link:
                self.info_panel.set_tcp_link(tcp_link)
                logger.info(f"TCP link set to: {tcp_link}")
            logger.info("Setting up IK widget")
            self.ik_widget.set_environment(self._env)
            self.ik_widget.set_scene_manager(self.render.scene)

            # Populate P2 widgets
            self._populate_p2_widgets()

            # Load ACM from environment if SRDF loaded
            if srdf:
                self._load_acm_from_env()

            self.statusBar().showMessage(f"Loaded: {urdf}")
            self._add_recent(str(Path(urdf).resolve()))
            logger.success(f"Successfully loaded: {urdf}")

            # Update TCP pose in status bar
            self._update_tcp_status({})

        except Exception as e:
            logger.exception(f"Failed to load: {e}")
            QMessageBox.critical(self, "Error", str(e))

    def _setup_joints(self):
        sg = self._env.getSceneGraph()
        movable = (JointType.REVOLUTE, JointType.CONTINUOUS, JointType.PRISMATIC)
        joints = {}
        for j in sg.getJoints():
            if j.type in movable:
                lim = j.limits
                lo, hi = (lim.lower, lim.upper) if lim else (-3.14, 3.14)
                joints[j.getName()] = (lo, hi, 0.0)
        self._joint_limits = joints  # Store for workspace/config operations
        self.manip_widget.set_joint_limits(joints)

    def _detect_tcp_link(self) -> str | None:
        """detect TCP link from SRDF or kinematic chain"""
        try:
            # try SRDF kinematic groups first
            kin_info = self._env.getKinematicsInformation()
            if kin_info and kin_info.chain_groups:
                group_names = list(kin_info.chain_groups.keys())
                if group_names:
                    kin_group = self._env.getKinematicGroup(group_names[0])
                    if kin_group:
                        tip_names = kin_group.getAllPossibleTipLinkNames()
                        if tip_names:
                            return tip_names[0]
        except Exception as e:
            logger.debug(f"failed to get TCP from SRDF: {e}")

        # fallback: look for common TCP link names
        try:
            sg = self._env.getSceneGraph()
            link_names = {link.getName() for link in sg.getLinks()}
            # Common TCP/tool link names in priority order
            for candidate in ["tool0", "tool_link", "tcp", "ee_link", "end_effector", "flange"]:
                if candidate in link_names:
                    return candidate
            # Try finding tip of chain (link with no child joints)
            child_links = {j.child_link_name for j in sg.getJoints()}
            parent_links = {j.parent_link_name for j in sg.getJoints()}
            tips = child_links - parent_links  # links that are children but not parents
            if tips:
                return sorted(tips)[-1]  # return last alphabetically (often tool0, link_6, etc)
        except Exception as e:
            logger.debug(f"failed to detect TCP: {e}")

        return None

    def _open_urdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open URDF", "", "URDF (*.urdf);;All (*)")
        if path:
            self.load(path)

    def _open_srdf(self):
        if not self._paths[0]:
            QMessageBox.information(self, "Info", "Load URDF first")
            return
        path, _ = QFileDialog.getOpenFileName(self, "Open SRDF", str(self._paths[0].parent), "SRDF (*.srdf)")
        if path:
            self.load(self._paths[0], path)

    def _add_recent(self, path: str):
        """Add to recent files."""
        recent = self._settings.value("recent", []) or []
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        self._settings.setValue("recent", recent[:10])
        self._update_recent_menu()

    def _update_recent_menu(self):
        """Update recent files menu."""
        recent = self._settings.value("recent", []) or []
        for i, act in enumerate(self._recent_actions):
            if i < len(recent):
                p = Path(recent[i])
                act.setText(f"{i+1}. {p.name}")
                act.setToolTip(str(p))
                act.setVisible(True)
            else:
                act.setVisible(False)
        self._recent_menu.setEnabled(len(recent) > 0)

    def _open_recent(self, idx: int):
        """Open recent file."""
        recent = self._settings.value("recent", []) or []
        if idx < len(recent):
            path = Path(recent[idx])
            if path.exists():
                self.load(path)
            else:
                QMessageBox.warning(self, "Not Found", f"File not found: {path}")
                recent.remove(str(path))
                self._settings.setValue("recent", recent)
                self._update_recent_menu()

    def _reload(self):
        if self._paths[0]:
            self.load(*self._paths)

    def _save_config(self):
        """Save joint config to JSON."""
        if not self._joint_limits:
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Config", "", "JSON (*.json)")
        if path:
            try:
                values = self.manip_widget.get_joint_values()
                path = Path(path)
                import json
                with path.open("w") as f:
                    json.dump(values, f, indent=2)
                self.statusBar().showMessage(f"Saved: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _load_config(self):
        """Load joint config from JSON."""
        if not self._joint_limits:
            return
        path, _ = QFileDialog.getOpenFileName(self, "Load Config", "", "JSON (*.json)")
        if path:
            try:
                path = Path(path)
                import json
                with path.open("r") as f:
                    values = json.load(f)
                self.manip_widget.set_joint_values(values)
                self.statusBar().showMessage(f"Loaded: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _save_pose(self):
        """Save current config as named pose."""
        if not self._joint_limits:
            return
        name, ok = QInputDialog.getText(self, "Save Pose", "Pose name:")
        if ok and name:
            values = self.manip_widget.get_joint_values()
            self.state_mgr.save_pose(name, values)
            self.statusBar().showMessage(f"Saved pose: {name}")

    def _load_pose(self):
        """Load named pose."""
        if not self._joint_limits:
            return
        poses = self.state_mgr.list_poses()
        if not poses:
            QMessageBox.information(self, "Info", "No saved poses")
            return
        name, ok = QInputDialog.getItem(self, "Load Pose", "Select pose:", poses, 0, False)
        if ok and name:
            values = self.state_mgr.load_pose(name)
            if values:
                self.manip_widget.set_joint_values(values)
                self.statusBar().showMessage(f"Loaded pose: {name}")


    def _load_trajectory(self):
        """Load trajectory via file dialog."""
        if not self._env:
            QMessageBox.information(self, "Info", "Load URDF first")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Trajectory", "", "JSON (*.json);;All (*)"
        )
        if path:
            self._load_trajectory_file(path)

    def _load_trajectory_file(self, path):
        """Load trajectory from JSON file path."""
        try:
            path = Path(path)
            import json
            with path.open("r") as f:
                data = json.load(f)

            # Handle both formats: [...] or {"trajectory": [...]}
            if isinstance(data, dict) and "trajectory" in data:
                data = data["trajectory"]

            # Convert JSON to trajectory format
            class Waypoint:
                def __init__(self, joints, time=0.0):
                    self.joints = joints
                    self.time = time

            trajectory = [Waypoint(wp.get("joints", {}), wp.get("time", 0.0)) for wp in data]
            self.traj_player.load_trajectory(trajectory)

            # Load into plot widget
            joint_names = list(self._joint_limits.keys()) if self._joint_limits else []
            if joint_names:
                self.plot.load_trajectory(data, joint_names)

            self.statusBar().showMessage(f"Loaded trajectory: {path} ({len(trajectory)} pts)")
            logger.info(f"Loaded {len(trajectory)} waypoints from {path}")

        except Exception as e:
            logger.exception(f"Failed to load trajectory: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load trajectory: {e}")

    def _on_trajectory_frame_changed(self, frame_idx: int):
        """Update joint values when trajectory frame changes."""
        waypoint = self.traj_player.get_waypoint()
        if waypoint:
            # Handle both dict and object waypoints
            joints = waypoint.get('joints') if isinstance(waypoint, dict) else getattr(waypoint, 'joints', None)
            if joints:
                self.manip_widget.set_joint_values(joints)

    def _export_screenshot(self):
        """Export screenshot as PNG."""
        path, _ = QFileDialog.getSaveFileName(self, "Export Screenshot", "", "PNG (*.png)")
        if path:
            try:
                self.render.save_screenshot(path)
                self.statusBar().showMessage(f"Saved: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _export_stl(self):
        """Export scene as STL."""
        path, _ = QFileDialog.getSaveFileName(self, "Export STL", "", "STL (*.stl)")
        if path:
            try:
                self.render.export_scene(path)
                self.statusBar().showMessage(f"Saved: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _export_obj(self):
        """Export scene as OBJ."""
        path, _ = QFileDialog.getSaveFileName(self, "Export OBJ", "", "OBJ (*.obj)")
        if path:
            try:
                self.render.export_scene(path)
                self.statusBar().showMessage(f"Saved: {path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def _show_workspace(self):
        """Sample and display robot workspace as point cloud."""
        if not self._env:
            QMessageBox.information(self, "Info", "Load URDF first")
            return

        if not self._joint_limits:
            QMessageBox.information(self, "Info", "No movable joints")
            return

        # Get joint names and limits from stored data
        joint_names = list(self._joint_limits.keys())
        joint_limits = {name: (lo, hi) for name, (lo, hi, _) in self._joint_limits.items()}

        # Get TCP link
        tcp_link = self.info_panel.tcp_link if hasattr(self.info_panel, 'tcp_link') else None
        if not tcp_link:
            QMessageBox.information(self, "Info", "No TCP link detected")
            return

        try:
            self.statusBar().showMessage("Sampling workspace (500 points)...")
            points = self.render.scene.sample_workspace(
                joint_names=joint_names,
                joint_limits=joint_limits,
                n_samples=500,
                tcp_link=tcp_link
            )

            if len(points) > 0:
                scalars = self.render.scene.compute_manipulability(points)
                self.render.scene.show_workspace(points, scalars, point_size=3.0)
                self.render.render()
                self.statusBar().showMessage(f"Workspace displayed: {len(points)} points")
            else:
                QMessageBox.warning(self, "Warning", "No workspace points generated")
                self.statusBar().clearMessage()

        except Exception as e:
            logger.exception(f"Workspace sampling failed: {e}")
            QMessageBox.critical(self, "Error", str(e))
            self.statusBar().clearMessage()

    def _clear_workspace(self):
        """Remove workspace visualization."""
        try:
            self.render.scene.hide_workspace()
            self.render.render()
            self.statusBar().showMessage("Workspace cleared")
        except Exception as e:
            logger.exception(f"Clear workspace failed: {e}")
            QMessageBox.critical(self, "Error", str(e))

    def _compute_contacts(self):
        """Compute and visualize contact results."""
        if not self._env:
            QMessageBox.information(self, "Info", "Load URDF first")
            return

        try:
            # Get discrete contact manager
            manager = self._env.getDiscreteContactManager()
            manager.setActiveCollisionObjects(self._env.getActiveLinkNames())

            # Set margin from widget
            margin = CollisionMarginData(self.contact_widget.contact_threshold.value())
            manager.setCollisionMarginData(margin)

            # Update transforms from current joint state
            state = self._env.getState()
            logger.debug(f"Contact check joints: {dict(state.joints)}")
            manager.setCollisionObjectsTransform(state.link_transforms)

            # Map contact test type from widget
            test_type_map = {
                "First": ContactTestType.FIRST,
                "Closest": ContactTestType.CLOSEST,
                "All": ContactTestType.ALL,
            }
            test_type = test_type_map[self.contact_widget.contact_test_type.currentText()]

            # Create contact request
            request = ContactRequest(test_type)

            # Execute check
            result_map = ContactResultMap()
            manager.contactTest(result_map, request)

            # Flatten results
            results = ContactResultVector()
            result_map.flattenMoveResults(results)

            if len(results) == 0:
                logger.success(f"No collisions detected")
            else:
                logger.warning(f"Found {len(results)} collision(s)")
            for i, contact in enumerate(results):
                logger.debug(f"Contact {i}: {contact.link_names[0]} <-> {contact.link_names[1]}, dist={contact.distance:.4f}")

            # Visualize
            self.render.scene.visualize_contacts(results)
            self.render.render()

            # Populate results table
            self.contact_widget.clear_results()
            for contact in results:
                self.contact_widget.add_result(
                    contact.link_names[0],
                    contact.link_names[1],
                    contact.distance,
                    contact.nearest_points[0],
                    contact.nearest_points[1],
                    contact.normal
                )
            self.contact_widget.set_result_count(len(results))

            self.statusBar().showMessage(f"Found {len(results)} contact(s)")

        except Exception as e:
            logger.exception(f"Contact computation failed: {e}")
            QMessageBox.critical(self, "Error", str(e))

    def _clear_contacts(self):
        """Clear contact visualization and results table."""
        self.render.scene.clear_contacts()
        self.render.render()
        self.contact_widget.clear_results()
        self.statusBar().showMessage("Contacts cleared")

    def _check_collisions_realtime(self, joint_values: dict[str, float]):
        """Real-time collision check on joint slider changes - highlights colliding links."""
        if not self._env:
            return

        try:
            manager = self._env.getDiscreteContactManager()
            if manager is None:
                return

            manager.setActiveCollisionObjects(self._env.getActiveLinkNames())
            manager.setCollisionMarginData(CollisionMarginData(0.0))  # No margin for real-time

            state = self._env.getState()
            manager.setCollisionObjectsTransform(state.link_transforms)

            request = ContactRequest(ContactTestType.FIRST)
            result_map = ContactResultMap()
            manager.contactTest(result_map, request)

            results = ContactResultVector()
            result_map.flattenMoveResults(results)

            # Collect colliding link names
            colliding_links = set()
            for contact in results:
                colliding_links.add(contact.link_names[0])
                colliding_links.add(contact.link_names[1])

            # Update link colors
            self.render.scene.highlight_collisions(colliding_links)
            self.render.render()

            if colliding_links:
                self.statusBar().showMessage(f"⚠ Collision: {', '.join(sorted(colliding_links))}")
            else:
                self.statusBar().showMessage("No collisions")

        except Exception:
            pass  # Silent fail for real-time check

    def _update_tcp_status(self, joint_values: dict[str, float]):
        """Update TCP pose in status bar."""
        if not self._env:
            logger.debug("_update_tcp_status: no env")
            return

        try:
            tcp_link = self.info_panel._tcp_link or "tool0"
            logger.debug(f"_update_tcp_status: tcp_link={tcp_link}")
            state = self._env.getState()
            if tcp_link in state.link_transforms:
                tf = state.link_transforms[tcp_link]
                t = tf.translation()
                # Extract RPY from rotation matrix
                import math
                m = tf.rotation()
                # Roll, Pitch, Yaw from rotation matrix
                if abs(m[2, 0]) < 0.9999:
                    pitch = -math.asin(m[2, 0])
                    roll = math.atan2(m[2, 1] / math.cos(pitch), m[2, 2] / math.cos(pitch))
                    yaw = math.atan2(m[1, 0] / math.cos(pitch), m[0, 0] / math.cos(pitch))
                else:
                    yaw = 0
                    if m[2, 0] < 0:
                        pitch = math.pi / 2
                        roll = math.atan2(m[0, 1], m[0, 2])
                    else:
                        pitch = -math.pi / 2
                        roll = math.atan2(-m[0, 1], -m[0, 2])

                text = (
                    f"TCP: X={t[0]:.3f} Y={t[1]:.3f} Z={t[2]:.3f} | "
                    f"R={math.degrees(roll):.1f}° P={math.degrees(pitch):.1f}° Y={math.degrees(yaw):.1f}°"
                )
                logger.debug(f"_update_tcp_status: setting text={text}")
                self._tcp_pose_label.setText(text)
            else:
                logger.debug(f"_update_tcp_status: {tcp_link} not in link_transforms")
        except Exception as e:
            logger.exception(f"_update_tcp_status error: {e}")

    def _delete_link(self, link_name: str):
        """Delete link from environment."""
        if not self._env:
            return

        try:
            # Can't delete root link
            sg = self._env.getSceneGraph()
            if link_name == sg.getRoot():
                QMessageBox.warning(self, "Warning", "Cannot delete root link")
                return

            # Confirm deletion
            reply = QMessageBox.question(
                self, "Delete Link",
                f"Delete link '{link_name}' and all children?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

            # Remove from environment
            if not self._env.removeLink(link_name):
                QMessageBox.warning(self, "Warning", f"Failed to remove link: {link_name}")
                return

            # Refresh visualization
            self.render.scene.remove_link(link_name)
            self.render.render()
            self.tree.load_environment(self._env)
            self.statusBar().showMessage(f"Deleted link: {link_name}")
            logger.info(f"Deleted link: {link_name}")

        except Exception as e:
            logger.exception(f"Failed to delete link: {e}")
            QMessageBox.critical(self, "Error", str(e))

    def _plan_motion(self, target):
        """Plan motion to target pose."""
        if not self._env:
            self.ik_widget.set_planning_status("No environment", False)
            return

        try:
            self.ik_widget.set_planning_status("Planning...")
            self.statusBar().showMessage("Planning motion...")

            from core.planning import PlanningHelper

            # Find task composer config
            config_path = None
            if self._paths[1]:  # SRDF loaded
                # Look for task_composer config in same directory
                srdf_dir = self._paths[1].parent
                for candidate in ["task_composer.yaml", "task_composer_config.yaml"]:
                    cfg = srdf_dir / candidate
                    if cfg.exists():
                        config_path = str(cfg)
                        break

            if not config_path:
                self.ik_widget.set_planning_status("No task composer config found", False)
                return

            # Create planner and execute
            planner = PlanningHelper(self._env, config_path)
            result = planner.plan_freespace([target])

            if result is None:
                self.ik_widget.set_planning_status("Planning failed", False)
                return

            # Extract trajectory
            trajectory = planner.extract_joint_trajectory(result)
            if not trajectory:
                self.ik_widget.set_planning_status("No trajectory in result", False)
                return

            # Load into player
            self.traj_player.load_trajectory(trajectory)

            # Load into plot
            joint_names = list(self._joint_limits.keys())
            traj_data = [{"time": wp.time, "joints": wp.joints} for wp in trajectory]
            self.plot.load_trajectory(traj_data, joint_names)

            self.ik_widget.set_planning_status(f"Success ({len(trajectory)} pts)", True)
            self.statusBar().showMessage(f"Motion planned: {len(trajectory)} waypoints")
            logger.info(f"Motion plan succeeded: {len(trajectory)} waypoints")

        except Exception as e:
            logger.exception(f"Motion planning failed: {e}")
            self.ik_widget.set_planning_status(f"Error: {str(e)[:30]}", False)

    def _on_pick_environment(self):
        """Handle environment picker button - show current URDF path."""
        if self._paths[0]:
            self.task_composer_widget.environment_line_edit.setText(str(self._paths[0]))
            self.statusBar().showMessage(f"Environment: {self._paths[0]}")
        else:
            self.statusBar().showMessage("No environment loaded - use File > Open URDF")

    def _execute_task_composer(self):
        """Execute motion planning via task composer."""
        if not self._env:
            self.task_composer_widget.log("Error: No environment loaded")
            self.statusBar().showMessage("No environment loaded")
            return

        try:
            from tesseract_robotics.planning import Robot, MotionProgram, CartesianTarget, Pose, TaskComposer

            self.task_composer_widget.clear_log()
            self.task_composer_widget.log("Starting task composer execution...")
            self.statusBar().showMessage("Executing task composer...")

            # Get current TCP link and pose
            tcp_link = getattr(self.info_panel, '_tcp_link', None)
            if not tcp_link:
                self.task_composer_widget.log("Error: No TCP link detected")
                return

            state = self._env.getState()
            current_tf = state.link_transforms.get(tcp_link)
            if not current_tf:
                self.task_composer_widget.log(f"Error: Cannot get pose for '{tcp_link}'")
                return

            # Create robot wrapper and composer
            robot = Robot(self._env, "manipulator")
            composer = TaskComposer.from_config()

            # Get joint state
            joint_names = robot.get_joint_names("manipulator")
            joint_vals = [state.joints.get(j, 0.0) for j in joint_names]

            self.task_composer_widget.log(f"TCP: {tcp_link}")
            self.task_composer_widget.log(f"Joints: {len(joint_names)}")

            # Create a simple motion: current -> offset -> current
            import numpy as np
            trans = current_tf.translation()
            # Small Z offset for demo motion
            target_pose = Pose.from_xyz_quat(trans[0], trans[1], trans[2] + 0.05, 0, 0, 0, 1)

            program = (MotionProgram("manipulator", tcp_frame=tcp_link, profile="DEFAULT")
                .move_to(CartesianTarget(target_pose, profile="DEFAULT")))

            # Use selected pipeline from widget
            pipeline = self.task_composer_widget.current_task() or "FreespacePipeline"
            self.task_composer_widget.log(f"Planning with {pipeline}...")
            result = composer.plan(robot, program, pipeline=pipeline)

            if result and result.successful:
                self.task_composer_widget.log(f"Success! {len(result)} waypoints")
                self.statusBar().showMessage(f"Planning succeeded: {len(result)} waypoints")

                # Extract trajectory for player
                traj_data = []
                for i, wp in enumerate(result):
                    traj_data.append({
                        "time": float(i) * 0.1,
                        "joints": {joint_names[j]: wp[j] for j in range(len(joint_names))}
                    })

                if traj_data:
                    self.plot.load_trajectory(traj_data, joint_names)
                    self.task_composer_widget.log("Trajectory loaded into plot")
            else:
                msg = result.message if result else "No result"
                self.task_composer_widget.log(f"Planning failed: {msg}")
                self.statusBar().showMessage("Planning failed")

        except Exception as e:
            logger.exception(f"Task composer failed: {e}")
            self.task_composer_widget.log(f"Error: {str(e)}")
            self.statusBar().showMessage(f"Failed: {str(e)[:50]}")

    def _on_acm_entry_added(self, link1: str, link2: str, reason: str):
        """Handle ACM entry added."""
        if not self._env:
            return
        try:
            acm = self._env.getAllowedCollisionMatrix()
            acm.addAllowedCollision(link1, link2, reason)
            self.statusBar().showMessage(f"ACM: Added {link1} <-> {link2}")
            logger.info(f"ACM entry added: {link1} <-> {link2} ({reason})")
        except Exception as e:
            logger.exception(f"Failed to add ACM entry: {e}")
            QMessageBox.critical(self, "Error", str(e))

    def _on_acm_entry_removed(self, link1: str, link2: str):
        """Handle ACM entry removed."""
        if not self._env:
            return
        try:
            acm = self._env.getAllowedCollisionMatrix()
            acm.removeAllowedCollision(link1, link2)
            self.statusBar().showMessage(f"ACM: Removed {link1} <-> {link2}")
            logger.info(f"ACM entry removed: {link1} <-> {link2}")
        except Exception as e:
            logger.exception(f"Failed to remove ACM entry: {e}")
            QMessageBox.critical(self, "Error", str(e))

    def _on_acm_generate(self, resolution: int):
        """Handle ACM generation request."""
        self.statusBar().showMessage(f"ACM generation requested (resolution: {resolution}) - not implemented yet")
        logger.info(f"ACM generation requested with resolution {resolution}")

    def _on_tcp_changed(self, link_name: str):
        """Handle TCP link change."""
        try:
            self.render.scene.set_tcp_link(link_name)
            self.info_panel.set_tcp_link(link_name)
            self.render.render()
            self.statusBar().showMessage(f"TCP set to: {link_name}")
            logger.info(f"TCP changed to: {link_name}")
        except Exception as e:
            logger.exception(f"Failed to set TCP: {e}")

    def _on_tcp_offset_changed(self, x: float, y: float, z: float, rx: float, ry: float, rz: float):
        """Handle TCP offset change."""
        self.statusBar().showMessage(f"TCP offset: [{x:.3f}, {y:.3f}, {z:.3f}] [{rx:.1f}°, {ry:.1f}°, {rz:.1f}°]")
        logger.info(f"TCP offset changed: pos=[{x}, {y}, {z}], rot=[{rx}, {ry}, {rz}]")

    def _on_kin_group_added(self, name: str, group_type: str, data: object):
        """Handle kinematic group added."""
        if not self._env:
            logger.warning("No environment loaded")
            return

        try:
            kin_info = self._env.getKinematicsInformation()

            if group_type == "chain":
                base_link, tip_link = data
                # addChainGroup(name, [(base, tip)])
                kin_info.addChainGroup(name, [(base_link, tip_link)])
                logger.info(f"Added chain group '{name}': {base_link} -> {tip_link}")

            elif group_type == "joints":
                # addJointGroup(name, [joints])
                kin_info.addJointGroup(name, list(data))
                logger.info(f"Added joint group '{name}': {data}")

            elif group_type == "links":
                # addLinkGroup(name, [links])
                kin_info.addLinkGroup(name, list(data))
                logger.info(f"Added link group '{name}': {data}")

            self.statusBar().showMessage(f"Group '{name}' ({group_type}) added")

            # Refresh group lists in other widgets
            groups = self._get_group_names()
            self.manip_widget.set_groups(groups)
            self.group_states_widget.set_groups(groups)

        except Exception as e:
            logger.error(f"Failed to add kinematic group: {e}")
            self.statusBar().showMessage(f"Failed to add group: {e}")

    def _on_kin_group_removed(self, name: str):
        """Handle kinematic group removed."""
        if not self._env:
            return

        try:
            kin_info = self._env.getKinematicsInformation()

            # Try to remove from all group types using proper methods
            removed = False
            if kin_info.hasChainGroup(name):
                kin_info.removeChainGroup(name)
                removed = True
            if kin_info.hasJointGroup(name):
                kin_info.removeJointGroup(name)
                removed = True
            if kin_info.hasLinkGroup(name):
                kin_info.removeLinkGroup(name)
                removed = True

            if removed:
                logger.info(f"Removed kinematic group: {name}")
                self.statusBar().showMessage(f"Group '{name}' removed")

                # Refresh group lists
                groups = self._get_group_names()
                self.manip_widget.set_groups(groups)
                self.group_states_widget.set_groups(groups)
            else:
                logger.warning(f"Group '{name}' not found")
                self.statusBar().showMessage(f"Group '{name}' not found")

        except Exception as e:
            logger.error(f"Failed to remove kinematic group: {e}")
            self.statusBar().showMessage(f"Failed to remove group: {e}")

    def _on_kin_group_modified(self):
        """Handle kinematic groups modified (Apply button)."""
        if not self._env:
            return

        try:
            # Refresh all widgets with current group info
            groups = self._get_group_names()
            self.manip_widget.set_groups(groups)
            self.group_states_widget.set_groups(groups)
            self._load_group_states_from_env()

            logger.info("Kinematic groups applied")
            self.statusBar().showMessage("Kinematic groups applied")

        except Exception as e:
            logger.error(f"Failed to apply kinematic groups: {e}")
            self.statusBar().showMessage(f"Failed to apply: {e}")

    def _on_group_state_added(self, group: str, state_name: str, values: dict):
        """Handle new state added - populate with current joint values."""
        try:
            current_values = self.manip_widget.get_joint_values()
            # Update the state with current joint values
            states = self.group_states_widget.get_states()
            if group in states and state_name in states[group]:
                states[group][state_name] = current_values
                self.group_states_widget.set_states(states)
            self.statusBar().showMessage(f"Added state '{state_name}' with current joint values")
            logger.info(f"Group state added: {group}/{state_name}")
        except Exception as e:
            logger.exception(f"Failed to add group state: {e}")

    def _on_group_state_applied(self, group: str, state_name: str):
        """Handle group state applied."""
        try:
            states = self.group_states_widget.get_states()
            if group in states and state_name in states[group]:
                joint_values = states[group][state_name]
                self.manip_widget.set_joint_values(joint_values)
                self.statusBar().showMessage(f"Applied state '{state_name}' for group '{group}'")
                logger.info(f"Group state applied: {group}/{state_name} with {len(joint_values)} joints")
            else:
                logger.warning(f"State not found: {group}/{state_name}")
        except Exception as e:
            logger.exception(f"Failed to apply group state: {e}")

    def _populate_p2_widgets(self):
        """Populate P2 widgets with environment data."""
        if not self._env:
            return

        try:
            sg = self._env.getSceneGraph()

            # Get all link names
            links = [link.getName() for link in sg.getLinks()]

            # Get all joint names
            movable = (JointType.REVOLUTE, JointType.CONTINUOUS, JointType.PRISMATIC)
            joints = [j.getName() for j in sg.getJoints() if j.type in movable]

            # Populate Kinematic Groups Editor
            self.kin_groups_widget.set_links(links)
            self.kin_groups_widget.set_joints(joints)

            # Populate ACM Editor with links for dropdown
            self.acm_widget.set_links(links)

            # Populate Manipulation Widget
            self.manip_widget.set_links(links)
            groups = self._get_group_names()
            logger.info(f"Setting groups for widgets: {groups}")
            self.manip_widget.set_groups(groups)

            # Populate Group States Editor
            self.group_states_widget.set_groups(groups)
            self._load_group_states_from_env()

            # Populate TCP Editor
            self.tcp_widget.set_links(links)
            tcp_link = self._detect_tcp_link()
            if tcp_link:
                self.tcp_widget.set_tcp(tcp_link)
                # Sync manip_widget TCP combo
                idx = self.manip_widget.tcp_combo_box.findText(tcp_link)
                if idx >= 0:
                    self.manip_widget.tcp_combo_box.setCurrentIndex(idx)

            # Populate Task Composer
            self._populate_task_composer()

            logger.info("P2 widgets populated")

        except Exception as e:
            logger.exception(f"Failed to populate P2 widgets: {e}")

    def _populate_task_composer(self):
        """Populate task composer widget with available pipelines."""
        try:
            from tesseract_robotics.planning import TaskComposer
            composer = TaskComposer.from_config()

            # Get available pipelines/tasks
            pipelines = [
                "FreespacePipeline",
                "CartesianPipeline",
                "TrajOptPipeline",
                "OMPLPipeline",
            ]
            self.task_composer_widget.set_tasks(pipelines, default="FreespacePipeline")

            # Set executors
            self.task_composer_widget.set_executors(["TaskflowExecutor"], default="TaskflowExecutor")

            # Set environment path
            if self._paths[0]:
                self.task_composer_widget.set_environment_name(str(self._paths[0].name))

            logger.info("Task composer populated")
        except Exception as e:
            logger.warning(f"Failed to populate task composer: {e}")

    def _load_group_states_from_env(self):
        """Load group states from SRDF into widget."""
        try:
            kin_info = self._env.getKinematicsInformation()
            if not kin_info or not hasattr(kin_info, 'group_states'):
                return

            states = {}  # {group: {state_name: {joint: value}}}
            for group_name, group_states in kin_info.group_states.items():
                if group_name not in states:
                    states[group_name] = {}
                for state_name, joint_state in group_states.items():
                    states[group_name][state_name] = dict(joint_state)

            self.group_states_widget.set_states(states)
            logger.info(f"Loaded {sum(len(s) for s in states.values())} group states from SRDF")
        except Exception as e:
            logger.exception(f"Failed to load group states: {e}")

    def _get_group_names(self) -> list[str]:
        """Get kinematic group names from environment."""
        try:
            kin_info = self._env.getKinematicsInformation()
            groups = []
            if kin_info:
                if hasattr(kin_info, 'chain_groups'):
                    groups.extend(kin_info.chain_groups.keys())
                if hasattr(kin_info, 'joint_groups'):
                    groups.extend(kin_info.joint_groups.keys())
                if hasattr(kin_info, 'link_groups'):
                    groups.extend(kin_info.link_groups.keys())
            logger.debug(f"Found kinematic groups: {groups}")
            return list(set(groups))
        except Exception as e:
            logger.exception(f"Failed to get group names: {e}")
            return []

    def _load_acm_from_env(self):
        """Populate ACM widget with entries from environment."""
        if not self._env:
            return
        try:
            acm = self._env.getAllowedCollisionMatrix()
            entries = []

            # getAllAllowedCollisions returns dict of (link1, link2) -> reason
            all_collisions = acm.getAllAllowedCollisions()
            for (link1, link2), reason in all_collisions.items():
                entries.append((link1, link2, reason or "From SRDF"))

            self.acm_widget.set_entries(entries)
            logger.info(f"Loaded {len(entries)} ACM entries from environment")
        except Exception as e:
            logger.error(f"Failed to load ACM from environment: {e}")

    def _setup_shortcuts(self):
        """Setup global keyboard shortcuts."""
        # View shortcuts
        QShortcut("Home", self, self.render.action_reset.trigger)
        QShortcut("F", self, self.render.action_fit.trigger)
        QShortcut("1", self, self.render.action_front.trigger)
        QShortcut("2", self, self.render.action_back.trigger)
        QShortcut("3", self, self.render.action_left.trigger)
        QShortcut("4", self, self.render.action_right.trigger)
        QShortcut("5", self, self.render.action_top.trigger)
        QShortcut("6", self, self.render.action_bottom.trigger)
        QShortcut("7", self, self.render.action_iso.trigger)
        QShortcut("G", self, self.render.action_grid.trigger)
        QShortcut("A", self, self.render.action_axes.trigger)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Tesseract Qt Viewer")
    parser.add_argument("urdf", nargs="?", help="URDF file path")
    parser.add_argument("srdf", nargs="?", help="SRDF file path")
    parser.add_argument("--trajectory", "-t", help="Trajectory JSON file to load")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    v = TesseractViewer()
    v.show()

    # macOS: VTK needs re-initialization after window is shown
    v.render.vtk_widget.Initialize()
    v.render.vtk_widget.Start()
    v.render.vtk_widget.GetRenderWindow().Render()

    # Bring window to front
    v.raise_()
    v.activateWindow()

    if args.urdf:
        v.load(args.urdf, args.srdf)
        v.render.vtk_widget.GetRenderWindow().Render()
    else:
        # Auto-load ABB robot from tesseract_support
        try:
            from pathlib import Path
            import tesseract_robotics
            logger.info("No URDF specified, loading default ABB IRB2400")
            support_dir = Path(tesseract_robotics.get_tesseract_support_path())
            urdf = support_dir / "urdf" / "abb_irb2400.urdf"
            srdf = support_dir / "urdf" / "abb_irb2400.srdf"
            if urdf.exists():
                v.load(str(urdf), str(srdf) if srdf.exists() else None)
                v.render.vtk_widget.GetRenderWindow().Render()
        except Exception as e:
            logger.warning(f"Could not auto-load ABB robot: {e}")

    if args.trajectory:
        v._load_trajectory_file(args.trajectory)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
